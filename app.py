import streamlit as st
import pandas as pd
from datetime import datetime, time, timedelta

st.set_page_config(
    page_title="Liquidador y Memoria de Nómina - Telemando",
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

st.title("⏱️ Liquidador y Memoria de Nómina - Telemando")
st.markdown("""
Herramienta optimizada para turnos **100% corridos**:
* **Registro Flexible:** Ingresa directamente la Fecha y Hora de Entrada y Salida, o sube tu plantilla Excel/CSV.
* **Cálculo Automático:** Detecta domingos, festivos y franja nocturna (**19:00 a 06:00**).
* **Memoria Mensual:** Almacena el histórico y te permite consultar y filtrar la liquidación por cada mes específico.
""")

with st.sidebar:
    st.header("⚙️ Parámetros Salariales")
    salario_base = st.number_input("Salario Mensual Básico (COP)", value=2500000, step=50000)
    aux_transporte = st.number_input("Auxilio de Transporte (COP)", value=162000, step=10000)
    divisor_horas = st.selectbox("Divisor Mensual de Horas", [182, 180, 200, 240], index=0)
    valor_hora_ordinaria = salario_base / divisor_horas
    st.info(f"💰 **Valor Hora Ordinaria:** $ {valor_hora_ordinaria:,.2f} COP")

tab1, tab2, tab3 = st.tabs(["📝 Registro y Carga de Excel", "🧮 Motor de Liquidación", "📊 Memoria y Consolidado Mensual"])

with tab1:
    st.subheader("1️⃣ Carga Masiva Mediante Plantilla Excel / CSV")
    with st.expander("📁 Subir Archivo de Turnos"):
        st.markdown("El archivo debe contener dos columnas exactas: **Entrada** y **Salida** (Ej: `2026-10-01 06:00:00`).")
        
        df_ejemplo = pd.DataFrame({
            "Entrada": ["2026-10-01 06:00:00", "2026-10-02 14:00:00", "2026-10-03 22:00:00"],
            "Salida": ["2026-10-01 14:00:00", "2026-10-02 22:00:00", "2026-10-04 06:00:00"]
        })
        st.download_button(
            label="📥 Descargar Plantilla de Ejemplo",
            data=df_ejemplo.to_csv(index=False).encode('utf-8'),
            file_name="plantilla_turnos_telemando.csv",
            mime="text/csv"
        )
        
        archivo = st.file_uploader("Selecciona tu archivo (.xlsx o .csv)", type=["csv", "xlsx"])
        if archivo is not None:
            try:
                if archivo.name.endswith('.csv'):
                    df_sub = pd.read_csv(archivo)
                else:
                    df_sub = pd.read_excel(archivo)
                
                nuevos = []
                for _, row in df_sub.iterrows():
                    dt_ini = pd.to_datetime(row["Entrada"])
                    dt_fin = pd.to_datetime(row["Salida"])
                    duracion = (dt_fin - dt_ini).total_seconds() / 3600.0
                    
                    es_dom = (dt_ini.weekday() == 6)
                    es_fes = (dt_ini.date() in obtener_festivos_colombia(dt_ini.year))
                    t_dia = "Domingo" if es_dom else ("Festivo" if es_fes else "Día Hábil")
                    
                    nuevos.append({
                        "Entrada": str(dt_ini),
                        "Salida": str(dt_fin),
                        "Tipo_Dia": t_dia,
                        "Horas": round(duracion, 2)
                    })
                
                df_n = pd.DataFrame(nuevos)
                if 'mis_turnos' in st.session_state:
                    st.session_state['mis_turnos'] = pd.concat([st.session_state['mis_turnos'], df_n], ignore_index=True)
                else:
                    st.session_state['mis_turnos'] = df_n
                st.success("¡Turnos cargados y guardados en memoria exitosamente desde el archivo!")
            except Exception as e:
                st.error(f"Error al procesar el archivo. Revisa que las columnas sean 'Entrada' y 'Salida'. Detalle: {e}")

    st.markdown("---")
    st.subheader("2️⃣ Registro Manual Directo (Turnos Corridos)")
    with st.form("form_manual_limpio", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_in = st.date_input("Fecha Entrada", value=datetime.today())
            h_in = st.time_input("Hora Entrada", value=time(6, 0))
        with col2:
            f_out = st.date_input("Fecha Salida", value=datetime.today())
            h_out = st.time_input("Hora Salida", value=time(14, 0))
            
        btn_add = st.form_submit_button("➕ Agregar Turno a la Memoria")
        
        if btn_add:
            dt_ini = datetime.combine(f_in, h_in)
            dt_fin = datetime.combine(f_out, h_out)
            
            if dt_fin <= dt_ini:
                st.error("Error: La fecha y hora de salida deben ser posteriores a la entrada.")
            else:
                duracion = (dt_fin - dt_ini).seconds / 3600.0 + ((dt_fin - dt_ini).days * 24)
                es_dom = (f_in.weekday() == 6)
                es_fes = (f_in in obtener_festivos_colombia(f_in.year))
                t_dia = "Domingo" if es_dom else ("Festivo" if es_fes else "Día Hábil")
                
                item = pd.DataFrame({
                    "Entrada": [str(dt_ini)],
                    "Salida": [str(dt_fin)],
                    "Tipo_Dia": [t_dia],
                    "Horas": [round(duracion, 2)]
                })
                
                if 'mis_turnos' in st.session_state:
                    st.session_state['mis_turnos'] = pd.concat([st.session_state['mis_turnos'], item], ignore_index=True)
                else:
                    st.session_state['mis_turnos'] = item
                st.success(f"¡Turno guardado! Duración: **{round(duracion, 2)} h** ({t_dia})")

    if 'mis_turnos' in st.session_state and not st.session_state['mis_turnos'].empty:
        st.write("### 📋 Historial de Turnos en Memoria:")
        st.dataframe(st.session_state['mis_turnos'], use_container_width=True)
        if st.button("🗑️ Borrar Toda la Memoria"):
            del st.session_state['mis_turnos']
            if 'resultado_final' in st.session_state:
                del st.session_state['resultado_final']
            st.rerun()

with tab2:
    st.subheader("🧮 Motor de Liquidación Automática")
    if 'mis_turnos' in st.session_state and not st.session_state['mis_turnos'].empty:
        if st.button("🚀 Procesar Liquidación de Turnos", type="primary"):
            val_hr = valor_hora_ordinaria
            detalles = []
            
            for _, r in st.session_state['mis_turnos'].iterrows():
                h_tot = r["Horas"]
                es_fd = r["Tipo_Dia"] in ["Domingo", "Festivo"]
                
                hr_ord = min(h_tot, 8.0)
                hr_ext = max(0.0, h_tot - 8.0)
                
                h_ini_t = datetime.strptime(str(r["Entrada"]), "%Y-%m-%d %H:%M:%S").time()
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
                    
                detalles.append({
                    "Entrada": r["Entrada"],
                    "Salida": r["Salida"],
                    "Tipo Día": r["Tipo_Dia"],
                    "Total Horas": h_tot,
                    "Ordinarias": hr_ord,
                    "Extras": hr_ext,
                    "Rec. Nocturno": round(rec_noc, 2),
                    "Subtotal (COP)": round(sub, 2)
                })
            
            df_res = pd.DataFrame(detalles)
            st.session_state['resultado_final'] = df_res
            st.success("¡Liquidación procesada con éxito!")
            st.dataframe(df_res, use_container_width=True)
    else:
        st.info("Registra o carga turnos en la primera pestaña para poder calcular.")

with tab3:
    st.subheader("📊 Memoria y Consulta por Mes Específico")
    if 'resultado_final' in st.session_state and not st.session_state['resultado_final'].empty:
        df_f = st.session_state['resultado_final']
        
        df_f['Mes_Anno'] = pd.to_datetime(df_f['Entrada']).dt.to_period('M').astype(str)
        meses_disp = sorted(df_f['Mes_Anno'].unique())
        
        mes_sel = st.selectbox("Selecciona el Periodo (Mes/Año) a Consultar", meses_disp)
        
        df_filtrado = df_f[df_f['Mes_Anno'] == mes_sel]
        
        st.write(f"### Detalle de Nómina para el Periodo: {mes_sel}")
        st.dataframe(df_filtrado.drop(columns=['Mes_Anno']), use_container_width=True)
        
        t_pagar = df_filtrado['Subtotal (COP)'].sum()
        t_hrs = df_filtrado['Total Horas'].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Horas Trabajadas", f"{t_hrs:.2f} h")
        with col2:
            st.metric(f"Devengado Estimado ({mes_sel})", f"$ {t_pagar:,.2f} COP")
            
        csv_dl = df_filtrado.drop(columns=['Mes_Anno']).to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Descargar Reporte del Mes ({mes_sel}) en CSV",
            data=csv_dl,
            file_name=f"nomina_telemando_{mes_sel}.csv",
            mime="text/csv"
        )
    else:
        st.info("Ejecuta la liquidación en la segunda pestaña para activar la memoria y los filtros mensuales.")
