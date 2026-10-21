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

st.title("⏱️ Liquidador y Memoria de Nómina - Telemando (Aguas de Cartagena)")
st.markdown("""
Herramienta optimizada para turnos **100% corridos**:
* **Carga Automática:** Lee tu reporte mensual (`Fecha Entrada`, `Hora`, `Fecha Salida`, `Hora.1`) reemplazando el historial para evitar duplicados.
* **Conceptos de Nómina Oficiales:** Consolidado exacto de **HED, HEN, HEDF, HENF, RN, RNF, HDF (Horas Festivas Habitual)**.
""")

with st.sidebar:
    st.header("⚙️ Parámetros Salariales")
    salario_base = st.number_input("Salario Mensual Básico (COP)", value=4570000, step=50000)
    aux_transporte = st.number_input("Auxilio de Transporte (COP)", value=162000, step=10000)
    divisor_horas = st.selectbox("Divisor Mensual de Horas", [182, 180, 200, 240], index=0)
    valor_hora_ordinaria = salario_base / divisor_horas
    st.info(f"💰 **Valor Hora Ordinaria:** $ {valor_hora_ordinaria:,.2f} COP")

tab1, tab2, tab3 = st.tabs(["📝 Carga de Reporte Excel", "🧮 Motor de Liquidación", "📊 Consolidado y Memoria Mensual"])

with tab1:
    st.subheader("1️⃣ Carga de Plantilla de Turnos (Excel / CSV)")
    with st.expander("📁 Subir Archivo"):
        st.markdown("Sube tu archivo con las columnas: **Fecha Entrada**, **Hora**, **Fecha Salida**, **Hora.1**.")
        
        archivo = st.file_uploader("Selecciona tu archivo (.xlsx o .csv)", type=["csv", "xlsx"])
        if archivo is not None:
            try:
                if archivo.name.endswith('.csv'):
                    df_sub = pd.read_csv(archivo)
                else:
                    df_sub = pd.read_excel(archivo)
                
                df_sub.columns = [str(c).strip() for c in df_sub.columns]
                nuevos = []
                
                if 'Fecha Entrada' in df_sub.columns and 'Hora' in df_sub.columns and 'Fecha Salida' in df_sub.columns and 'Hora.1' in df_sub.columns:
                    for _, row in df_sub.iterrows():
                        if pd.isna(row['Fecha Entrada']) or pd.isna(row['Hora']) or pd.isna(row['Fecha Salida']) or pd.isna(row['Hora.1']):
                            continue
                        
                        f_in = pd.to_datetime(row['Fecha Entrada']).date()
                        h_in = row['Hora']
                        if isinstance(h_in, str):
                            t_in = datetime.strptime(h_in, '%H:%M:%S').time() if len(h_in) >= 5 else time(0, 0)
                        elif hasattr(h_in, 'hour'):
                            t_in = h_in
                        else:
                            t_in = (datetime.min + pd.to_timedelta(h_in)).time()
                            
                        f_out = pd.to_datetime(row['Fecha Salida']).date()
                        h_out = row['Hora.1']
                        if isinstance(h_out, str):
                            t_out = datetime.strptime(h_out, '%H:%M:%S').time() if len(h_out) >= 5 else time(0, 0)
                        elif hasattr(h_out, 'hour'):
                            t_out = h_out
                        else:
                            t_out = (datetime.min + pd.to_timedelta(h_out)).time()
                            
                        dt_ini = datetime.combine(f_in, t_in)
                        dt_fin = datetime.combine(f_out, t_out)
                        
                        duracion = (dt_fin - dt_ini).total_seconds() / 3600.0
                        es_dom = (dt_ini.weekday() == 6)
                        es_fes = (dt_ini.date() in obtener_festivos_colombia(dt_ini.year))
                        t_dia = "Domingo/Festivo" if (es_dom or es_fes) else "Día Hábil"
                        
                        nuevos.append({
                            "Entrada": str(dt_ini),
                            "Salida": str(dt_fin),
                            "Tipo_Dia": t_dia,
                            "Horas": round(duracion, 2)
                        })
                elif 'Entrada' in df_sub.columns and 'Salida' in df_sub.columns:
                    for _, row in df_sub.iterrows():
                        if pd.isna(row['Entrada']) or pd.isna(row['Salida']):
                            continue
                        dt_ini = pd.to_datetime(row["Entrada"])
                        dt_fin = pd.to_datetime(row["Salida"])
                        duracion = (dt_fin - dt_ini).total_seconds() / 3600.0
                        
                        es_dom = (dt_ini.weekday() == 6)
                        es_fes = (dt_ini.date() in obtener_festivos_colombia(dt_ini.year))
                        t_dia = "Domingo/Festivo" if (es_dom or es_fes) else "Día Hábil"
                        
                        nuevos.append({
                            "Entrada": str(dt_ini),
                            "Salida": str(dt_fin),
                            "Tipo_Dia": t_dia,
                            "Horas": round(duracion, 2)
                        })
                else:
                    st.error("El archivo no tiene las columnas esperadas.")
                
                if nuevos:
                    df_n = pd.DataFrame(nuevos)
                    st.session_state['mis_turnos'] = df_n
                    st.success(f"¡Se cargaron {len(nuevos)} turnos exitosamente! Historial actualizado.")
            except Exception as e:
                st.error(f"Error al procesar el archivo: {e}")

    st.markdown("---")
    st.subheader("2️⃣ Registro Manual de Turno")
    with st.form("form_manual", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            f_in = st.date_input("Fecha Entrada", value=datetime.today())
            h_in = st.time_input("Hora Entrada", value=time(6, 0))
        with col2:
            f_out = st.date_input("Fecha Salida", value=datetime.today())
            h_out = st.time_input("Hora Salida", value=time(14, 0))
            
        btn_add = st.form_submit_button("➕ Agregar Turno")
        if btn_add:
            dt_ini = datetime.combine(f_in, h_in)
            dt_fin = datetime.combine(f_out, h_out)
            if dt_fin <= dt_ini:
                st.error("La salida debe ser posterior a la entrada.")
            else:
                duracion = (dt_fin - dt_ini).seconds / 3600.0 + ((dt_fin - dt_ini).days * 24)
                es_dom = (f_in.weekday() == 6)
                es_fes = (f_in in obtener_festivos_colombia(f_in.year))
                t_dia = "Domingo/Festivo" if (es_dom or es_fes) else "Día Hábil"
                
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
                st.success(f"¡Turno guardado ({round(duracion, 2)} h)!")

    if 'mis_turnos' in st.session_state and not st.session_state['mis_turnos'].empty:
        st.write("### 📋 Historial de Turnos en Memoria:")
        st.dataframe(st.session_state['mis_turnos'], use_container_width=True)
        if st.button("🗑️ Borrar Historial"):
            del st.session_state['mis_turnos']
            if 'resultado_final' in st.session_state:
                del st.session_state['resultado_final']
            st.rerun()

with tab2:
    st.subheader("🧮 Motor de Liquidación y Desglose Oficial (Aguas de Cartagena)")
    if 'mis_turnos' in st.session_state and not st.session_state['mis_turnos'].empty:
        if st.button("🚀 Procesar Liquidación Oficial", type="primary"):
            val_hr = valor_hora_ordinaria
            detalles = []
            
            for _, r in st.session_state['mis_turnos'].iterrows():
                dt_ini = datetime.strptime(str(r["Entrada"]), "%Y-%m-%d %H:%M:%S")
                dt_fin = datetime.strptime(str(r["Salida"]), "%Y-%m-%d %H:%M:%S")
                h_tot = r["Horas"]
                es_fd = r["Tipo_Dia"] == "Domingo/Festivo"
                
                hr_ord = min(h_tot, 8.0)
                hr_ext = max(0.0, h_tot - 8.0)
                h_ini_t = dt_ini.time()
                
                hed, hen, hedf, henf, rn, rnf, hdf = 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
                
                if not es_fd:
                    if h_ini_t >= time(22, 0) or h_ini_t < time(6, 0):
                        rn = min(h_tot, 8.0)
                    elif h_ini_t >= time(14, 0) and h_ini_t < time(22, 0):
                        rn = min(3.0, h_tot)
                    
                    if hr_ext > 0:
                        if h_ini_t >= time(22, 0) or h_ini_t < time(6, 0):
                            hen = hr_ext
                        else:
                            hed = hr_ext
                else:
                    if h_ini_t >= time(22, 0) or h_ini_t < time(6, 0):
                        rnf = min(h_tot, 8.0)
                    else:
                        hdf = min(hr_ord, 8.0)
                    
                    if hr_ext > 0:
                        if h_ini_t >= time(22, 0) or h_ini_t < time(6, 0):
                            henf = hr_ext
                        else:
                            hedf = hr_ext

                sub = (hr_ord * val_hr) + (hed * val_hr * 1.25) + (hen * val_hr * 1.75) + \
                      (hedf * val_hr * 2.0) + (henf * val_hr * 2.5) + \
                      (rn * val_hr * 0.35) + (rnf * val_hr * 1.35) + (hdf * val_hr * 0.75)
                    
                detalles.append({
                    "Entrada": r["Entrada"],
                    "Salida": r["Salida"],
                    "Tipo Día": r["Tipo_Dia"],
                    "Total Horas": h_tot,
                    "HED": round(hed, 2),
                    "HEN": round(hen, 2),
                    "HEDF": round(hedf, 2),
                    "HENF": round(henf, 2),
                    "RN": round(rn, 2),
                    "RNF": round(rnf, 2),
                    "HDF (Fest. Hab.)": round(hdf, 2),
                    "Subtotal (COP)": round(sub, 2)
                })
            
            df_res = pd.DataFrame(detalles)
            st.session_state['resultado_final'] = df_res
            st.success("¡Liquidación oficial procesada correctamente!")
            st.dataframe(df_res, use_container_width=True)
    else:
        st.info("Registra o carga turnos en la primera pestaña.")

with tab3:
    st.subheader("📊 Consolidado Oficial por Conceptos (Memoria Mensual)")
    if 'resultado_final' in st.session_state and not st.session_state['resultado_final'].empty:
        df_f = st.session_state['resultado_final']
        df_f['Mes_Anno'] = pd.to_datetime(df_f['Entrada']).dt.to_period('M').astype(str)
        meses_disp = sorted(df_f['Mes_Anno'].unique())
        
        mes_sel = st.selectbox("Selecciona el Periodo (Mes/Año) a Consultar", meses_disp)
        df_filtrado = df_f[df_f['Mes_Anno'] == mes_sel]
        
        st.write(f"### Detalle para el Periodo: {mes_sel}")
        st.dataframe(df_filtrado.drop(columns=['Mes_Anno']), use_container_width=True)
        
        tot_hed = df_filtrado['HED'].sum()
        tot_hen = df_filtrado['HEN'].sum()
        tot_hedf = df_filtrado['HEDF'].sum()
        tot_henf = df_filtrado['HENF'].sum()
        tot_rn = df_filtrado['RN'].sum()
        tot_rnf = df_filtrado['RNF'].sum()
        tot_hdf = df_filtrado['HDF (Fest. Hab.)'].sum()
        tot_pagar = df_filtrado['Subtotal (COP)'].sum()
        tot_hrs = df_filtrado['Total Horas'].sum()
        
        st.markdown("### 📋 Consolidado Oficial (Aguas de Cartagena)")
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            st.metric("Total Horas Trabajadas", f"{tot_hrs:.2f} h")
            st.metric("HORAS EXTRAS DIURNAS (HED)", f"{tot_hed:.2f} h")
            st.metric("HORAS EXTRAS NOCTURNAS (HEN)", f"{tot_hen:.2f} h")
        with col_c2:
            st.metric("EXTRAS DIURNAS DOM/FEST (HEDF)", f"{tot_hedf:.2f} h")
            st.metric("EXTRAS NOCTURNAS DOM/FES (HENF)", f"{tot_henf:.2f} h")
            st.metric("RECARGO NOCTURNO (RN)", f"{tot_rn:.2f} h")
        with col_c3:
            st.metric("RECARGO NOCTURNO DOM/FES (RNF)", f"{tot_rnf:.2f} h")
            st.metric("FESTIVAS HABITUAL (HDF)", f"{tot_hdf:.2f} h")
            st.metric(f"💰 Devengado ({mes_sel})", f"$ {tot_pagar:,.2f} COP")
            
        csv_dl = df_filtrado.drop(columns=['Mes_Anno']).to_csv(index=False).encode('utf-8')
        st.download_button(
            label=f"📥 Descargar Consolidado Oficial ({mes_sel}) en CSV",
            data=csv_dl,
            file_name=f"consolidado_oficial_{mes_sel}.csv",
            mime="text/csv"
        )
    else:
        st.info("Procesa la liquidación en la segunda pestaña para ver el consolidado mensual.")
