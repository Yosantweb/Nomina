import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(
    page_title="Liquidador de Turnos - Telemando",
    page_icon="⏱️",
    layout="wide"
)

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

    festivos.add(siguiente_lunes(datetime(ano, 1, 6).date()))
    festivos.add(siguiente_lunes(datetime(ano, 3, 19).date()))
    festivos.add(siguiente_lunes(datetime(ano, 6, 29).date()))
    festivos.add(siguiente_lunes(datetime(ano, 8, 15).date()))
    festivos.add(siguiente_lunes(datetime(ano, 10, 12).date()))
    festivos.add(siguiente_lunes(datetime(ano, 11, 1).date()))
    festivos.add(siguiente_lunes(datetime(ano, 11, 11).date()))
    
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
    
    festivos.add(domingo_pascua - timedelta(days=3))
    festivos.add(domingo_pascua - timedelta(days=2))
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=43)))
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=64)))
    festivos.add(siguiente_lunes(domingo_pascua + timedelta(days=71)))
    return festivos

st.title("⏱️ Liquidador de Turnos Corridos - Telemando")
st.markdown("Herramienta limpia y directa: solo ingresa **Fecha/Hora de Entrada** y **Fecha/Hora de Salida** (turnos 100% corridos).")

with st.sidebar:
    st.header("⚙️ Parámetros Salariales")
    salario_base = st.number_input("Salario Mensual Básico (COP)", value=2500000, step=50000)
    aux_transporte = st.number_input("Auxilio de Transporte (COP)", value=162000, step=10000)
    divisor_horas = st.selectbox("Divisor Mensual de Horas", [182, 180, 200, 240], index=0)
    valor_hora_ordinaria = salario_base / divisor_horas
    st.info(f"💰 **Valor Hora:** $ {valor_hora_ordinaria:,.2f} COP")

tab1, tab2, tab3 = st.tabs(["📝 Registrar Turno", "🧮 Calcular Recargos", "📊 Consolidado"])

with tab1:
    st.subheader("Ingresa los datos de tu turno")
    with st.form("form_directo_limpio", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_in = st.date_input("Fecha Entrada", value=datetime.today())
            h_in = st.time_input("Hora Entrada", value=time(6, 0))
        with col2:
            f_out = st.date_input("Fecha Salida", value=datetime.today())
            h_out = st.time_input("Hora Salida", value=time(14, 0))
            
        enviar = st.form_submit_button("➕ Agregar Turno")
        
        if enviar:
            dt_ini = datetime.combine(f_in, h_in)
            dt_fin = datetime.combine(f_out, h_out)
            
            if dt_fin <= dt_ini:
                st.error("La fecha y hora de salida deben ser posteriores a la entrada.")
            else:
                duracion = (dt_fin - dt_ini).seconds / 3600.0 + ((dt_fin - dt_ini).days * 24)
                
                es_domingo = (f_in.weekday() == 6)
                es_festivo = (f_in in obtener_festivos_colombia(f_in.year))
                tipo_dia = "Domingo" if es_domingo else ("Festivo" if es_festivo else "Día Hábil")
                
                item = pd.DataFrame({
                    "Entrada": [str(dt_ini)],
                    "Salida": [str(dt_fin)],
                    "Tipo_Dia": [tipo_dia],
                    "Horas": [round(duracion, 2)]
                })
                
                if 'mis_turnos' in st.session_state:
                    st.session_state['mis_turnos'] = pd.concat([st.session_state['mis_turnos'], item], ignore_index=True)
                else:
                    st.session_state['mis_turnos'] = item
                st.success(f"¡Turno registrado! Duración: {round(duracion, 2)} h ({tipo_dia})")

    if 'mis_turnos' in st.session_state and not st.session_state['mis_turnos'].empty:
        st.dataframe(st.session_state['mis_turnos'], use_container_width=True)
        if st.button("🗑️ Borrar Todo"):
            del st.session_state['mis_turnos']
            st.rerun()

with tab2:
    st.subheader("🧮 Motor de Liquidación")
    if 'mis_turnos' in st.session_state and not st.session_state['mis_turnos'].empty:
        if st.button("🚀 Calcular Liquidación", type="primary"):
            val_hr = valor_hora_ordinaria
            res = []
            for _, r in st.session_state['mis_turnos'].iterrows():
                h_tot = r["Horas"]
                es_fd = r["Tipo_Dia"] in ["Domingo", "Festivo"]
                
                hr_ord = min(h_tot, 8.0)
                hr_ext = max(0.0, h_tot - 8.0)
                
                h_ini_t = datetime.strptime(r["Entrada"], "%Y-%m-%d %H:%M:%S").time()
                rec_noc = 0.0
                if h_ini_t >= time(14, 0) and h_ini_t < time(18, 0):
                    rec_noc = min(3.0, h_tot)
                elif h_ini_t >= time(21, 0) or h_ini_t < time(6, 0):
                    rec_noc = min(h_tot, 8.0)
                elif h_ini_t >= time(18, 0) and h_ini_t <= time(20, 0):
                    rec_noc = min(11.0, h_tot)
                
                sub = (hr_ord * val_hr) + (rec_noc * val_hr * 0.35) + (hr_ext * val_hr * (1.75 if es_fd else 1.25))
                if es_fd and hr_ord > 0:
                    sub += hr_ord * val_hr * 0.75
                    
                res.append({
                    "Entrada": r["Entrada"],
                    "Salida": r["Salida"],
                    "Tipo Día": r["Tipo_Dia"],
                    "Total Horas": h_tot,
                    "Ordinarias": hr_ord,
                    "Extras": hr_ext,
                    "Rec. Nocturno": round(rec_noc, 2),
                    "Subtotal (COP)": round(sub, 2)
                })
            df_final = pd.DataFrame(res)
            st.session_state['resultado_final'] = df_final
            st.dataframe(df_final, use_container_width=True)
    else:
        st.info("Registra turnos primero.")

with tab3:
    st.subheader("📊 Reporte y Consolidado")
    if 'resultado_final' in st.session_state and not st.session_state['resultado_final'].empty:
        df_f = st.session_state['resultado_final']
        st.metric("Total Devengado Estimado", f"$ {df_f['Subtotal (COP)'].sum():,.2f} COP")
        st.download_button("📥 Descargar CSV", df_f.to_csv(index=False).encode('utf-8'), "nomina.csv", "text/csv")
    else:
        st.info("Ejecuta la liquidación en la pestaña anterior.")
