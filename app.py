import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(
    page_title="Calculadora de Recargos y Horas Extras - Telemando",
    page_icon="⏱️",
    layout="wide"
)

st.title("⏱️ Calculadora y Liquidador de Turnos y Recargos")
st.markdown("""
Herramienta diseñada para operadores de turnos rotativos bajo la legislación laboral colombiana (jornada semanal máxima de **42 horas**).
Permite calcular con precisión la distribución de horas ordinarias, recargos nocturnos (HRN), horas extras diurnas (HED) y nocturnas (HEN), dominicales y festivos.
""")

with st.sidebar:
    st.header("⚙️ Parámetros Salariales y Legales")
    salario_base = st.number_input("Salario Mensual Básico (COP)", value=2500000, step=50000)
    aux_transporte = st.number_input("Auxilio de Transporte (COP)", value=162000, step=10000)
    
    # Divisor mensual para jornada de 42 horas (ej. 182 horas mensuales estándar)
    divisor_horas = st.selectbox("Divisor Mensual de Horas", [182, 180, 200, 240], index=0)
    valor_hora_ordinaria = salario_base / divisor_horas
    
    st.info(f"💰 **Valor Hora Ordinaria:** $ {valor_hora_ordinaria:,.2f} COP")

tab1, tab2, tab3 = st.tabs(["📝 Registro de Turnos", "🧮 Motor de Cálculo", "📊 Reporte Consolidado"])

with tab1:
    st.subheader("Ingresa tus turnos trabajados del mes")
    
    with st.form("form_turno", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_turno = st.date_input("Fecha del Turno", value=datetime.today())
            tipo_dia = st.selectbox("Tipo de Día", ["Día Hábil (Ordinario)", "Domingo o Festivo"])
        with col2:
            h_inicio = st.time_input("Hora de Inicio", value=time(6, 0))
            h_fin = st.time_input("Hora de Fin", value=time(14, 0))
        with col3:
            descanso = st.selectbox("Descanso / Almuerzo", ["Turno Corrido (Sin descuento)", "Descontar 1 hora de descanso"])
            
        btn_agregar = st.form_submit_button("➕ Agregar Turno")
        
        if btn_agregar:
            dt_ini = datetime.combine(fecha_turno, h_inicio)
            dt_fin = datetime.combine(fecha_turno, h_fin)
            if dt_fin <= dt_ini:
                dt_fin += timedelta(days=1)
                
            duracion = (dt_fin - dt_ini).seconds / 3600.0
            if descanso == "Descontar 1 hora de descanso":
                duracion = max(0.0, duracion - 1.0)
                
            nuevo_item = pd.DataFrame({
                "Fecha": [str(fecha_turno)],
                "Tipo_Dia": [tipo_dia],
                "Hora_Inicio": [h_inicio.strftime("%H:%M")],
                "Hora_Fin": [h_fin.strftime("%H:%M")],
                "Total_Horas": [round(duracion, 2)]
            })
            
            if 'df_turnos_usuario' in st.session_state:
                st.session_state['df_turnos_usuario'] = pd.concat([st.session_state['df_turnos_usuario'], nuevo_item], ignore_index=True)
            else:
                st.session_state['df_turnos_usuario'] = nuevo_item
            st.success("¡Turno agregado correctamente!")

    if 'df_turnos_usuario' in st.session_state and not st.session_state['df_turnos_usuario'].empty:
        st.write("### Turnos Registrados:")
        st.dataframe(st.session_state['df_turnos_usuario'], use_container_width=True)
        
        if st.button("🗑️ Borrar Todos los Turnos"):
            del st.session_state['df_turnos_usuario']
            st.rerun()

with tab2:
    st.subheader("🧮 Cálculo de Horas y Recargos")
    if 'df_turnos_usuario' in st.session_state and not st.session_state['df_turnos_usuario'].empty:
        if st.button("🚀 Ejecutar Liquidación", type="primary"):
            val_hr = valor_hora_ordinaria
            detalles = []
            
            for idx, row in st.session_state['df_turnos_usuario'].iterrows():
                h_tot = row["Total_Horas"]
                es_festivo = "Festivo" in row["Tipo_Dia"]
                
                # Desglose base operativo
                hr_ord = min(h_tot, 8.0)
                hr_ext = max(0.0, h_tot - 8.0)
                
                # Identificación de recargo nocturno (ej. turnos que entran en la tarde o noche)
                rec_noc = 3.0 if row["Hora_Inicio"] in ["14:00", "22:00", "15:00", "23:00"] else 0.0
                
                # Valores económicos
                pago_ord = hr_ord * val_hr
                pago_rec_noc = rec_noc * val_hr * 0.35
                pago_ext = hr_ext * val_hr * (1.75 if es_festivo else 1.25)
                
                subtotal = pago_ord + pago_rec_noc + pago_ext
                if es_festivo and hr_ord > 0:
                    subtotal += hr_ord * val_hr * 0.75 # Recargo dominical/festivo
                    
                detalles.append({
                    "Fecha": row["Fecha"],
                    "Tipo Día": row["Tipo_Dia"],
                    "Horas Turno": h_tot,
                    "H. Ordinarias": hr_ord,
                    "H. Extras": hr_ext,
                    "Rec. Nocturno (h)": rec_noc,
                    "Subtotal Est. (COP)": round(subtotal, 2)
                })
                
            df_res = pd.DataFrame(detalles)
            st.session_state['df_res'] = df_res
            st.success("¡Liquidación procesada con éxito!")
            st.dataframe(df_res, use_container_width=True)
    else:
        st.info("Agrega turnos en la primera pestaña para poder calcular.")

with tab3:
    st.subheader("📊 Consolidado Mensual")
    if 'df_res' in st.session_state and not st.session_state['df_res'].empty:
        df_final = st.session_state['df_res']
        total_pagar = df_final["Subtotal Est. (COP)"].sum()
        total_hrs = df_final["Horas Turno"].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Horas Trabajadas", f"{total_hrs:.2f} h")
        with col2:
            st.metric("Devengado Estimado Turnos", f"$ {total_pagar:,.2f} COP")
            
        csv_export = df_final.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar Reporte en CSV",
            data=csv_export,
            file_name="reporte_nomina_telemando.csv",
            mime="text/csv"
        )
    else:
        st.info("Ejecuta la liquidación en la pestaña anterior para ver el consolidado.")
