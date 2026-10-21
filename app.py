import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(
    page_title="Calculadora de Recargos y Turnos - Telemando",
    page_icon="⏱️",
    layout="wide"
)

# Función para calcular los días festivos oficiales de Colombia para un año determinado
def obtener_festivos_colombia(ano):
    festivos = set()
    
    # Festivos fijos
    festivos.add(datetime(ano, 1, 1).date())   # Año Nuevo
    festivos.add(datetime(ano, 5, 1).date())   # Día del Trabajo
    festivos.add(datetime(ano, 7, 20).date())  # Independencia
    festivos.add(datetime(ano, 8, 7).date())   # Batalla de Boyacá
    festivos.add(datetime(ano, 12, 8).date())  # Inmaculada Concepción
    festivos.add(datetime(ano, 12, 25).date()) # Navidad
    
    # Función auxiliar para el festivo de la ley "Emiliani" (trasladar al lunes siguiente si cae entre semana)
    def siguiente_lunes(fec):
        dias_hasta_lunes = (0 - fec.weekday()) % 7
        if dias_hasta_lunes == 0:
            return fec
        return fec + timedelta(days=dias_hasta_lunes)

    festivos.add(siguiente_lunes(datetime(ano, 1, 6).date()))   # Reyes Magos
    festivos.add(siguiente_lunes(datetime(ano, 3, 19).date()))  # San José
    festivos.add(siguiente_lunes(datetime(ano, 6, 29).date()))  # San Pedro y San Pablo
    festivos.add(siguiente_lunes(datetime(ano, 8, 15).date()))  # Asunción de la Virgen
    festivos.add(siguiente_lunes(datetime(ano, 10, 12).date())) # Día de la Raza
    festivos.add(siguiente_lunes(datetime(ano, 11, 1).date()))  # Todos los Santos
    festivos.add(siguiente_lunes(datetime(ano, 11, 11).date())) # Independencia de Cartagena
    
    # Cálculo de Pascua (Algoritmo de Meeus/Jones/Butcher)
    a = ano % 19
    b = ano // 100
    c = ano % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes_pascua = (h + l - 7 * m + 114) // 31
    dia_pascua = ((h + l - 7 * m + 114) % 31) + 1
    
    domingo_pascua = datetime(ano, mes_pascua, dia_pascua).date()
    
    # Festivos basados en Pascua
    festivos.add(domingo_pascua - timedelta(days=3)) # Jueves Santo
    festivos.add(domingo_pascua - timedelta(days=2)) # Viernes Santo
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=43))) # Ascensión del Señor
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=64))) # Corpus Christi
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=71))) # Sagrado Corazón
    
    return festivos

st.title("⏱️ Calculadora y Liquidador Automático de Turnos y Recargos")
st.markdown("""
Herramienta adaptada a la **legislación laboral colombiana vigente**:
* **Jornada Laboral:** Basada en la normativa actual de **42 horas semanales**.
* **Franja Nocturna:** El recargo nocturno ordinario aplica de **7:00 p.m. a 6:00 a.m.** del día siguiente (según la actualización de la reforma laboral).
* **Festivos y Domingos:** El sistema **detecta automáticamente** si la fecha seleccionada corresponde a un domingo o festivo oficial de Colombia.
""")

with st.sidebar:
    st.header("⚙️ Parámetros Salariales")
    salario_base = st.number_input("Salario Mensual Básico (COP)", value=2500000, step=50000)
    aux_transporte = st.number_input("Auxilio de Transporte (COP)", value=162000, step=10000)
    
    divisor_horas = st.selectbox("Divisor Mensual de Horas", [182, 180, 200, 240], index=0)
    valor_hora_ordinaria = salario_base / divisor_horas
    
    st.info(f"💰 **Valor Hora Ordinaria:** $ {valor_hora_ordinaria:,.2f} COP")

tab1, tab2, tab3 = st.tabs(["📝 Registro de Turnos", "🧮 Motor de Cálculo", "📊 Reporte Consolidado"])

with tab1:
    st.subheader("Ingresa tus turnos trabajados del mes")
    st.markdown("*(El sistema determina automáticamente si el día es Domingo o Festivo)*")
    
    with st.form("form_turno", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            fecha_turno = st.date_input("Fecha del Turno", value=datetime.today())
        with col2:
            h_inicio = st.time_input("Hora de Inicio", value=time(6, 0))
            h_fin = st.time_input("Hora de Fin", value=time(14, 0))
        with col3:
            descanso = st.selectbox("Descanso / Almuerzo", ["Turno Corrido (Sin descuento)", "Descontar 1 hora de descanso"])
            
        btn_agregar = st.form_submit_button("➕ Agregar Turno")
        
        if btn_agregar:
            # Determinación automática del tipo de día
            f_date = fecha_turno
            es_domingo = (f_date.weekday() == 6)
            festivos_ano = obtener_festivos_colombia(f_date.year)
            es_festivo = (f_date in festivos_ano)
            
            if es_domingo:
                tipo_dia_str = "Domingo"
            elif es_festivo:
                tipo_dia_str = "Festivo"
            else:
                tipo_dia_str = "Día Hábil (Ordinario)"
                
            dt_ini = datetime.combine(f_date, h_inicio)
            dt_fin = datetime.combine(f_date, h_fin)
            if dt_fin <= dt_ini:
                dt_fin += timedelta(days=1)
                
            duracion = (dt_fin - dt_ini).seconds / 3600.0
            if descanso == "Descontar 1 hora de descanso":
                duracion = max(0.0, duracion - 1.0)
                
            nuevo_item = pd.DataFrame({
                "Fecha": [str(f_date)],
                "Tipo_Dia": [tipo_dia_str],
                "Hora_Inicio": [h_inicio.strftime("%H:%M")],
                "Hora_Fin": [h_fin.strftime("%H:%M")],
                "Total_Horas": [round(duracion, 2)]
            })
            
            if 'df_turnos_usuario' in st.session_state:
                st.session_state['df_turnos_usuario'] = pd.concat([st.session_state['df_turnos_usuario'], nuevo_item], ignore_index=True)
            else:
                st.session_state['df_turnos_usuario'] = nuevo_item
            st.success(f"¡Turno agregado correctamente! Detectado como: **{tipo_dia_str}**")

    if 'df_turnos_usuario' in st.session_state and not st.session_state['df_turnos_usuario'].empty:
        st.write("### Turnos Registrados:")
        st.dataframe(st.session_state['df_turnos_usuario'], use_container_width=True)
        
        if st.button("🗑️ Borrar Todos los Turnos"):
            del st.session_state['df_turnos_usuario']
            st.rerun()

with tab2:
    st.subheader("🧮 Cálculo de Horas y Recargos (Franja Nocturna 7:00 p.m. a 6:00 a.m.)")
    if 'df_turnos_usuario' in st.session_state and not st.session_state['df_turnos_usuario'].empty:
        if st.button("🚀 Ejecutar Liquidación", type="primary"):
            val_hr = valor_hora_ordinaria
            detalles = []
            
            for idx, row in st.session_state['df_turnos_usuario'].iterrows():
                h_tot = row["Total_Horas"]
                tipo_d = row["Tipo_Dia"]
                es_festivo_dom = (tipo_d in ["Domingo", "Festivo"])
                
                # Desglose base operativo
                hr_ord = min(h_tot, 8.0)
                hr_ext = max(0.0, h_tot - 8.0)
                
                # Cálculo preciso o estimación de recargo nocturno bajo la franja 7:00 p.m. a 6:00 a.m.
                # Evaluamos si el turno abarca horas dentro del rango 19:00 a 06:00
                h_ini_obj = datetime.strptime(row["Hora_Inicio"], "%H:%M").time()
                
                # Turno tarde/noche (ej. de 14:00 a 22:00 -> de 19:00 a 22:00 son 3 horas nocturnas)
                # Turno noche (ej. de 22:00 a 06:00 -> 8 horas nocturnas)
                rec_noc = 0.0
                if h_ini_obj >= time(14, 0) and h_ini_obj < time(22, 0):
                    rec_noc = 3.0 # Típico turno de tarde con 3h nocturnas (19:00 a 22:00)
                elif h_ini_obj >= time(22, 0) or h_ini_obj < time(6, 0):
                    rec_noc = min(h_tot, 8.0) # Turno nocturno completo
                
                # Valores económicos con la nueva franja y recargos de ley
                pago_ord = hr_ord * val_hr
                pago_rec_noc = rec_noc * val_hr * 0.35
                pago_ext = hr_ext * val_hr * (1.75 if es_festivo_dom else 1.25)
                
                subtotal = pago_ord + pago_rec_noc + pago_ext
                if es_festivo_dom and hr_ord > 0:
                    subtotal += hr_ord * val_hr * 0.75 # Recargo adicional dominical/festivo
                    
                detalles.append({
                    "Fecha": row["Fecha"],
                    "Tipo Día": tipo_d,
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
