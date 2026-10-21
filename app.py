import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(
    page_title="Calculadora de Turnos y Recargos - Telemando",
    page_icon="⏱️",
    layout="wide"
)

# Función para calcular los días festivos oficiales de Colombia
def obtener_festivos_colombia(ano):
    festivos = set()
    festivos.add(datetime(ano, 1, 1).date())   # Año Nuevo
    festivos.add(datetime(ano, 5, 1).date())   # Día del Trabajo
    festivos.add(datetime(ano, 7, 20).date())  # Independencia
    festivos.add(datetime(ano, 8, 7).date())   # Batalla de Boyacá
    festivos.add(datetime(ano, 12, 8).date())  # Inmaculada Concepción
    festivos.add(datetime(ano, 12, 25).date()) # Navidad
    
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
    
    # Pascua
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
    
    festivos.add(domingo_pascua - timedelta(days=3)) # Jueves Santo
    festivos.add(domingo_pascua - timedelta(days=2)) # Viernes Santo
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=43))) # Ascensión
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=64))) # Corpus Christi
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=71))) # Sagrado Corazón
    
    return festivos

st.title("⏱️ Calculadora y Liquidador Automático por Rango de Fecha y Hora")
st.markdown("""
Herramienta libre y flexible para turnos rotativos (8h, 12h o personalizados) bajo la legislación colombiana (jornada de **42 horas semanales**):
* **Cálculo por Fecha y Hora:** Ingresa fecha/hora de entrada y fecha/hora de salida. El sistema calcula las horas exactas.
* **Días Especiales:** Detecta automáticamente si el turno cae en Domingo o Festivo.
* **Franja Nocturna:** Recargo nocturno computado rigurosamente de **7:00 p.m. (19:00) a 6:00 a.m.** del día siguiente.
""")

with st.sidebar:
    st.header("⚙️ Parámetros Salariales")
    salario_base = st.number_input("Salario Mensual Básico (COP)", value=2500000, step=50000)
    aux_transporte = st.number_input("Auxilio de Transporte (COP)", value=162000, step=10000)
    divisor_horas = st.selectbox("Divisor Mensual de Horas", [182, 180, 200, 240], index=0)
    valor_hora_ordinaria = salario_base / divisor_horas
    
    st.info(f"💰 **Valor Hora Ordinaria:** $ {valor_hora_ordinaria:,.2f} COP")

tab1, tab2, tab3 = st.tabs(["📝 Registro por Entrada/Salida", "🧮 Motor de Cálculo", "📊 Reporte Consolidado"])

with tab1:
    st.subheader("Registra tu turno indicando Fecha y Hora de Entrada y Salida")
    
    with st.form("form_turno_flexible", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            fecha_inicio = st.date_input("Fecha de Entrada", value=datetime.today())
            h_inicio = st.time_input("Hora de Entrada", value=time(6, 0))
        with col2:
            fecha_fin = st.date_input("Fecha de Salida", value=datetime.today())
            h_fin = st.time_input("Hora de Salida", value=time(14, 0))
            
        descanso = st.selectbox("Descanso / Almuerzo", ["Turno Corrido (Sin descuento)", "Descontar 1 hora de descanso"])
            
        btn_agregar = st.form_submit_button("➕ Agregar Turno al Registro")
        
        if btn_agregar:
            dt_ini = datetime.combine(fecha_inicio, h_inicio)
            dt_fin = datetime.combine(fecha_fin, h_fin)
            
            if dt_fin <= dt_ini:
                st.error("Error: La fecha y hora de salida deben ser posteriores a la entrada.")
            else:
                duracion = (dt_fin - dt_ini).seconds / 3600.0 + ((dt_fin - dt_ini).days * 24)
                if descanso == "Descontar 1 hora de descanso":
                    duracion = max(0.0, duracion - 1.0)
                
                # Detectar tipo de día basado en la fecha de entrada
                f_date = fecha_inicio
                es_domingo = (f_date.weekday() == 6)
                festivos_ano = obtener_festivos_colombia(f_date.year)
                es_festivo = (f_date in festivos_ano)
                
                if es_domingo:
                    tipo_dia_str = "Domingo"
                elif es_festivo:
                    tipo_dia_str = "Festivo"
                else:
                    tipo_dia_str = "Día Hábil (Ordinario)"
                
                nuevo_item = pd.DataFrame({
                    "F_Inicio": [str(dt_ini)],
                    "F_Fin": [str(dt_fin)],
                    "Tipo_Dia": [tipo_dia_str],
                    "Total_Horas": [round(duracion, 2)]
                })
                
                if 'df_turnos_flex' in st.session_state:
                    st.session_state['df_turnos_flex'] = pd.concat([st.session_state['df_turnos_flex'], nuevo_item], ignore_index=True)
                else:
                    st.session_state['df_turnos_flex'] = nuevo_item
                st.success(f"¡Turno agregado con éxito! Duración: **{round(duracion, 2)} horas** ({tipo_dia_str})")

    if 'df_turnos_flex' in st.session_state and not st.session_state['df_turnos_flex'].empty:
        st.write("### Listado de Turnos Registrados:")
        st.dataframe(st.session_state['df_turnos_flex'], use_container_width=True)
        
        if st.button("🗑️ Borrar Todos los Turnos"):
            del st.session_state['df_turnos_flex']
            st.rerun()

with tab2:
    st.subheader("🧮 Cálculo de Horas y Recargos (Franja Nocturna 19:00 a 06:00)")
    if 'df_turnos_flex' in st.session_state and not st.session_state['df_turnos_flex'].empty:
        if st.button("🚀 Ejecutar Liquidación Detallada", type="primary"):
            val_hr = valor_hora_ordinaria
            detalles = []
            
            for idx, row in st.session_state['df_turnos_flex'].iterrows():
                h_tot = row["Total_Horas"]
                tipo_d = row["Tipo_Dia"]
                es_festivo_dom = (tipo_d in ["Domingo", "Festivo"])
                
                # Jornada ordinaria vs extras (referencia 8h diarias por turno estándar)
                hr_ord = min(h_tot, 8.0)
                hr_ext = max(0.0, h_tot - 8.0)
                
                # Estimación inteligente de recargo nocturno basada en la duración y hora de entrada
                dt_ini_parsed = datetime.strptime(row["F_Inicio"], "%Y-%m-%d %H:%M:%S")
                h_ini_time = dt_ini_parsed.time()
                
                rec_noc = 0.0
                # Si entra a las 14:00 (turno tarde 8h) -> 3h nocturnas (19:00 a 22:00)
                # Si entra a las 22:00 (turno noche 8h) -> 8h nocturnas
                # Si entra a las 19:00 (turno noche 12h) -> 11h nocturnas (19:00 a 06:00)
                if h_ini_time >= time(14, 0) and h_ini_time < time(18, 0):
                    rec_noc = min(3.0, h_tot)
                elif h_ini_time >= time(21, 0) or h_ini_time < time(6, 0):
                    rec_noc = min(h_tot, 8.0)
                elif h_ini_time >= time(18, 0) and h_ini_time <= time(20, 0):
                    rec_noc = min(11.0, h_tot - 1.0) if h_tot > 11 else min(11.0, h_tot)
                
                # Valores económicos
                pago_ord = hr_ord * val_hr
                pago_rec_noc = rec_noc * val_hr * 0.35
                pago_ext = hr_ext * val_hr * (1.75 if es_festivo_dom else 1.25)
                
                subtotal = pago_ord + pago_rec_noc + pago_ext
                if es_festivo_dom and hr_ord > 0:
                    subtotal += hr_ord * val_hr * 0.75 # Recargo dominical/festivo
                    
                detalles.append({
                    "Entrada": row["F_Inicio"],
                    "Salida": row["F_Fin"],
                    "Tipo Día": tipo_d,
                    "Horas Turno": h_tot,
                    "H. Ordinarias": hr_ord,
                    "H. Extras": hr_ext,
                    "Rec. Nocturno (h)": round(rec_noc, 2),
                    "Subtotal Est. (COP)": round(subtotal, 2)
                })
                
            df_res = pd.DataFrame(detalles)
            st.session_state['df_res_flex'] = df_res
            st.success("¡Liquidación procesada con éxito!")
            st.dataframe(df_res, use_container_width=True)
    else:
        st.info("Registra turnos en la primera pestaña para poder calcular.")

with tab3:
    st.subheader("📊 Consolidado Mensual")
    if 'df_res_flex' in st.session_state and not st.session_state['df_res_flex'].empty:
        df_final = st.session_state['df_res_flex']
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
