import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import timedelta
import numpy as np

# ============================================================
# CONFIG
# ============================================================
st.set_page_config(
    page_title="Tablero de Control – Gestión Comercial TAT",
    page_icon="⭐",
    layout="wide",
    initial_sidebar_state="collapsed",
)

MES_ORDER = {
    'Enero': 1, 'Febrero': 2, 'Marzo': 3, 'Abril': 4,
    'Mayo': 5, 'Junio': 6, 'Julio': 7, 'Agosto': 8,
    'Septiembre': 9, 'Octubre': 10, 'Noviembre': 11, 'Diciembre': 12
}

# ============================================================
# CSS
# ============================================================
st.markdown("""
<style>
    section[data-testid="stSidebar"] { display: none; }
    .main .block-container { padding-top: 0.5rem; max-width: 1420px; }
    .dash-header {
        background: linear-gradient(135deg, #1e1e2f 0%, #2d2d44 100%);
        color: #ffffff; padding: 16px 28px; border-radius: 12px; margin-bottom: 10px;
    }
    .dash-header h1 { margin:0; font-size:1.4rem; font-weight:700; }
    .dash-header p { margin:2px 0 0 0; font-size:.8rem; opacity:.72; }
    .filter-bar {
        background: #ffffff; border: 1px solid #ddd;
        border-radius: 10px; padding: 12px 18px; margin-bottom: 14px;
        box-shadow: 0 1px 4px rgba(0,0,0,.04);
    }
    .filter-bar label, .filter-bar .stSelectbox label, .filter-bar .stMultiSelect label {
        font-size: .72rem !important; font-weight: 600 !important;
        color: #6c757d !important; text-transform: uppercase; letter-spacing: .3px;
    }
    .kpi-card {
        background: #ffffff; border-radius: 12px; padding: 14px 10px;
        text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,.06);
        border-left: 5px solid; height: 105px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .kpi-title { font-size: .62rem; font-weight: 600; color: #6c757d; text-transform: uppercase; letter-spacing: .3px; margin-bottom: 2px; }
    .kpi-value { font-size: 1.25rem; font-weight: 800; margin: 0; line-height: 1.2; }
    .kpi-sub { font-size: .6rem; color: #999; margin-top: 2px; }
    .section-title {
        font-size: .92rem; font-weight: 700; color: #1e1e2f;
        border-bottom: 2px solid #2563eb; display: inline-block;
        padding-bottom: 4px; margin: 16px 0 10px 0;
    }
    .chart-card {
        background: #ffffff; border-radius: 12px; padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,.06);
        border: 1px solid #e0e0e0; margin-bottom: 14px;
    }
    .chart-card h4 {
        font-size: .82rem; font-weight: 600; color: #1e1e2f;
        margin: 0 0 8px 0; padding-bottom: 6px; border-bottom: 1px solid #e0e0e0;
    }
    .chart-tag {
        display:inline-block; background:#eef2ff; color:#4338ca;
        font-size:.62rem; padding:1px 7px; border-radius:4px; margin-left:6px; font-weight:500;
    }
    .footer { text-align:center; color:#6c757d; font-size:.7rem; margin-top:20px; padding:10px; }
</style>
""", unsafe_allow_html=True)

ACCENT = ['#2563eb', '#059669', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#e11d48', '#f59e0b']
PIE_COLORS = ['#2563eb','#059669','#d97706','#dc2626','#7c3aed','#0891b2','#e11d48','#f97316',
              '#14b8a6','#8b5cf6','#ec4899','#06b6d4','#84cc16','#f43f5e','#a855f7','#22d3ee',
              '#facc15','#fb923c','#a3e635']

def base_layout(height=360):
    return dict(
        plot_bgcolor='white', paper_bgcolor='white',
        font=dict(color='#333', size=11),
        margin=dict(l=20, r=20, t=30, b=20),
        height=height,
    )

# ============================================================
# DATA LOADING
# ============================================================
@st.cache_data
def load_data():
    path = "data.xlsx"
    ventas = pd.read_excel(path, sheet_name='Ventas')
    impactos = pd.read_excel(path, sheet_name='IMPACTOS')
    pdv_master = pd.read_excel(path, sheet_name='PDV')

    # Dates - Ventas
    ventas['MES_NUM'] = ventas['MES'].map(MES_ORDER)
    ventas['FECHA'] = pd.to_datetime(
        ventas['AÑO'].astype(str) + '-' + ventas['MES_NUM'].astype(str).str.zfill(2) + '-' + ventas['DIA'].astype(str).str.zfill(2),
        errors='coerce')
    ventas['MES_LABEL'] = ventas['FECHA'].dt.strftime('%Y-%m')

    # Dates - Impactos
    impactos['MES_NUM'] = impactos['MES'].map(MES_ORDER)
    impactos['FECHA'] = pd.to_datetime(
        impactos['AÑO'].astype(str) + '-' + impactos['MES_NUM'].astype(str).str.zfill(2) + '-' + impactos['DIA'].astype(str).str.zfill(2),
        errors='coerce')
    impactos['MES_LABEL'] = impactos['FECHA'].dt.strftime('%Y-%m')

    # Visit Duration
    def parse_time(s):
        try:
            parts = str(s).split(':')
            return timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2]))
        except:
            return pd.NaT
    impactos['HORA_TD'] = impactos['HORA'].apply(parse_time)
    impactos['HORA_SALIDA_TD'] = impactos['HORA SALIDA'].apply(parse_time)
    impactos['DURACION_MIN'] = (impactos['HORA_SALIDA_TD'] - impactos['HORA_TD']).dt.total_seconds() / 60
    impactos.loc[impactos['DURACION_MIN'] <= 0, 'DURACION_MIN'] = np.nan

    # Clean PDV
    pdv_master['Categoria'] = pdv_master['Categoria'].astype(str).str.upper().str.strip()
    pdv_master.loc[pdv_master['Categoria'].isin(['NAN', 'NONE', '']), 'Categoria'] = 'SIN CATEGORÍA'
    pdv_master['ACTIVO'] = pdv_master['Estado'].apply(lambda x: x == 1)

    # Join Categoria from PDV master
    pdv_lookup = pdv_master[['Nombre', 'Categoria', 'Zona']].drop_duplicates(subset='Nombre', keep='first')
    pdv_lookup = pdv_lookup.rename(columns={'Nombre': 'PDV'})
    ventas = ventas.merge(pdv_lookup[['PDV', 'Categoria', 'Zona']], on='PDV', how='left')
    ventas['Categoria'] = ventas['Categoria'].fillna('SIN CATEGORÍA')
    impactos = impactos.merge(pdv_lookup[['PDV', 'Categoria']], on='PDV', how='left')
    impactos['Categoria'] = impactos['Categoria'].fillna('SIN CATEGORÍA')

    return ventas, impactos, pdv_master

ventas_raw, impactos_raw, pdv_master = load_data()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="dash-header">
    <h1>⭐ Tablero de Control – Gestión Comercial TAT</h1>
    <p>Análisis integral de ventas, efectividad operativa y cobertura de campo</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# TOP FILTER BAR (6 filters)
# ============================================================
st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
fc1, fc2, fc3, fc4, fc5, fc6 = st.columns(6)

with fc1:
    ciudades = sorted(set(ventas_raw['CIUDAD'].dropna().unique().tolist() + impactos_raw['CIUDAD'].dropna().unique().tolist()))
    sel_ciudad = st.multiselect("🏙️ Ciudad", ciudades, default=[], key='f_ciudad')
with fc2:
    marcas = sorted(ventas_raw['MARCA'].dropna().unique().tolist())
    sel_marca = st.multiselect("🏷️ Marca", marcas, default=[], key='f_marca')
with fc3:
    cats = sorted(set(ventas_raw['Categoria'].dropna().unique().tolist()))
    sel_cat = st.multiselect("📂 Categoría", cats, default=[], key='f_cat')
with fc4:
    meses = sorted(set(ventas_raw['MES_LABEL'].dropna().unique().tolist() + impactos_raw['MES_LABEL'].dropna().unique().tolist()))
    sel_mes = st.multiselect("📅 Mes", meses, default=[], key='f_mes')
with fc5:
    zonas = sorted(impactos_raw['ZONA'].dropna().unique().tolist())
    sel_zona = st.multiselect("📍 Zona", zonas, default=[], key='f_zona')
with fc6:
    mercs = sorted(set(ventas_raw['MERCADERISTA'].dropna().unique().tolist() + impactos_raw['MERCADERISTA'].dropna().unique().tolist()))
    sel_merc = st.multiselect("👤 Mercaderista", mercs, default=[], key='f_merc')

st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# APPLY FILTERS
# ============================================================
v = ventas_raw.copy()
imp = impactos_raw.copy()

if sel_ciudad:
    v = v[v['CIUDAD'].isin(sel_ciudad)]
    imp = imp[imp['CIUDAD'].isin(sel_ciudad)]
if sel_marca:
    v = v[v['MARCA'].isin(sel_marca)]
if sel_cat:
    v = v[v['Categoria'].isin(sel_cat)]
    imp = imp[imp['Categoria'].isin(sel_cat)]
if sel_mes:
    v = v[v['MES_LABEL'].isin(sel_mes)]
    imp = imp[imp['MES_LABEL'].isin(sel_mes)]
if sel_zona:
    imp = imp[imp['ZONA'].isin(sel_zona)]
    mercs_in_zone = imp['MERCADERISTA'].unique()
    v = v[v['MERCADERISTA'].isin(mercs_in_zone)]
if sel_merc:
    v = v[v['MERCADERISTA'].isin(sel_merc)]
    imp = imp[imp['MERCADERISTA'].isin(sel_merc)]

# ============================================================
# KPI CALCULATIONS (CORRECTED)
# ============================================================
total_ventas = v['VALOR'].sum()
total_pdv_universe = pdv_master['Nombre'].nunique()
total_visitas = len(imp)
pdv_visitados = imp['PDV'].nunique()

# Ticket = ventas / líneas de producto (como el Excel original)
num_lineas = len(v)
ticket_promedio = total_ventas / num_lineas if num_lineas > 0 else 0

# Time effectiveness
total_active_hours = imp['DURACION_MIN'].sum() / 60 if imp['DURACION_MIN'].sum() > 0 else 0
efect_hora = total_ventas / total_active_hours if total_active_hours > 0 else 0

# Strike Rate
visits_set = set(zip(imp['PDV'], imp['MERCADERISTA'], imp['FECHA'].dt.date))
sales_set = set(zip(v['PDV'], v['MERCADERISTA'], v['FECHA'].dt.date))
with_sale = len(visits_set & sales_set)
strike_rate = (with_sale / len(visits_set) * 100) if len(visits_set) > 0 else 0

# Coverage
active_pdvs = pdv_master[pdv_master['ACTIVO']]['Nombre'].nunique()
coverage = (pdv_visitados / active_pdvs * 100) if active_pdvs > 0 else 0

# ============================================================
# KPI CARDS (8)
# ============================================================
st.markdown('<div class="section-title">📊 Indicadores Clave de Rendimiento</div>', unsafe_allow_html=True)

kpi_data = [
    ("Ventas Totales", f"${total_ventas:,.2f}", f"Acum. {num_lineas:,} líneas", ACCENT[0]),
    ("Universo PDV", f"{total_pdv_universe:,}", "Base maestra total", ACCENT[1]),
    ("PDV Visitados", f"{pdv_visitados:,}", "Puntos con impacto", '#0891b2'),
    ("Total Visitas", f"{total_visitas:,}", "Impactos registrados", ACCENT[7]),
    ("% Efectividad", f"{strike_rate:.1f}%", "Visitas con venta", ACCENT[3]),
    ("Ticket Promedio", f"${ticket_promedio:,.2f}", "Por línea de producto", ACCENT[2]),
    ("Cobertura", f"{coverage:.1f}%", f"{pdv_visitados:,} de {active_pdvs:,}", ACCENT[4]),
    ("$/Hora en PDV", f"${efect_hora:,.2f}", "Efectividad temporal", ACCENT[6]),
]

cols_kpi = st.columns(8)
for i, (title, value, sub, color) in enumerate(kpi_data):
    with cols_kpi[i]:
        st.markdown(f"""
        <div class="kpi-card" style="border-left-color:{color};">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value" style="color:{color};">{value}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

# ============================================================
# SECTION 2: SALES
# ============================================================
st.markdown('<div class="section-title">📈 Análisis de Ventas</div>', unsafe_allow_html=True)

c2a, c2b = st.columns(2)

with c2a:
    st.markdown('<div class="chart-card"><h4>📈 Evolución Mensual por Mercaderista <span class="chart-tag">Líneas</span></h4>', unsafe_allow_html=True)
    evo = v.groupby(['MES_LABEL', 'MERCADERISTA'], as_index=False)['VALOR'].sum().sort_values('MES_LABEL')
    if not evo.empty:
        fig = px.line(evo, x='MES_LABEL', y='VALOR', color='MERCADERISTA', markers=True,
                      color_discrete_sequence=ACCENT,
                      labels={'MES_LABEL': 'Mes', 'VALOR': 'Ventas ($)', 'MERCADERISTA': 'Vendedor'})
        fig.update_layout(**base_layout(340), legend=dict(orientation='h', yanchor='bottom', y=-0.32, font=dict(size=9)),
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(gridcolor='#eee'))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2b:
    st.markdown('<div class="chart-card"><h4>🏙️ Ventas por Ciudad <span class="chart-tag">Barras</span></h4>', unsafe_allow_html=True)
    vc = v.groupby('CIUDAD', as_index=False)['VALOR'].sum().sort_values('VALOR', ascending=True)
    if not vc.empty:
        fig = px.bar(vc, y='CIUDAD', x='VALOR', orientation='h',
                     text=vc['VALOR'].apply(lambda x: f"${x:,.0f}"),
                     color='VALOR', color_continuous_scale='Blues',
                     labels={'VALOR': 'Ventas ($)', 'CIUDAD': ''})
        fig.update_layout(**base_layout(max(340, len(vc)*18)), showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(tickfont=dict(size=9), gridcolor='#eee'))
        fig.update_traces(textposition='outside', textfont_size=8)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

c2c, c2d = st.columns(2)

with c2c:
    st.markdown('<div class="chart-card"><h4>🏷️ Ventas por Marca <span class="chart-tag">Donut</span></h4>', unsafe_allow_html=True)
    vm = v.groupby('MARCA', as_index=False)['VALOR'].sum().sort_values('VALOR', ascending=False)
    if not vm.empty:
        fig = px.pie(vm, names='MARCA', values='VALOR', hole=0.5, color_discrete_sequence=PIE_COLORS)
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(size=10),
                          margin=dict(l=10, r=10, t=20, b=10), height=370, showlegend=True,
                          legend=dict(font=dict(size=8)))
        fig.update_traces(textposition='inside', textinfo='percent', textfont_size=8)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c2d:
    st.markdown('<div class="chart-card"><h4>📂 Ventas por Categoría <span class="chart-tag">Barras</span></h4>', unsafe_allow_html=True)
    vcat = v.groupby('Categoria', as_index=False)['VALOR'].sum().sort_values('VALOR', ascending=True)
    if not vcat.empty:
        fig = px.bar(vcat, y='Categoria', x='VALOR', orientation='h',
                     text=vcat['VALOR'].apply(lambda x: f"${x:,.0f}"),
                     color='VALOR', color_continuous_scale='Purples',
                     labels={'VALOR': 'Ventas ($)', 'Categoria': ''})
        fig.update_layout(**base_layout(340), showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(gridcolor='#eee'))
        fig.update_traces(textposition='outside', textfont_size=10)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SECTION 3: EFFECTIVENESS
# ============================================================
st.markdown('<div class="section-title">⏱️ Análisis de Efectividad y Tiempo</div>', unsafe_allow_html=True)

c3a, c3b = st.columns(2)

with c3a:
    st.markdown('<div class="chart-card"><h4>⏱️ Ventas vs Tiempo en PDV <span class="chart-tag">Dispersión</span></h4>', unsafe_allow_html=True)
    imp_agg = imp.groupby('MERCADERISTA', as_index=False).agg(avg_min=('DURACION_MIN', 'mean'), visits=('PDV', 'count'))
    v_agg = v.groupby('MERCADERISTA', as_index=False)['VALOR'].sum()
    scatter_df = imp_agg.merge(v_agg, on='MERCADERISTA', how='left').fillna(0)
    if not scatter_df.empty and scatter_df['avg_min'].sum() > 0:
        fig = px.scatter(scatter_df, x='avg_min', y='VALOR', size='visits', color='MERCADERISTA',
                         hover_name='MERCADERISTA', size_max=50, color_discrete_sequence=ACCENT,
                         labels={'avg_min': 'Duración Prom. Visita (min)', 'VALOR': 'Ventas Totales ($)'})
        fig.update_layout(**base_layout(360), legend=dict(orientation='h', yanchor='bottom', y=-0.30, font=dict(size=9)),
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(gridcolor='#eee'))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c3b:
    st.markdown('<div class="chart-card"><h4>🎯 Efectividad de Visitas <span class="chart-tag">Gauge</span></h4>', unsafe_allow_html=True)
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta", value=strike_rate,
        number={'suffix': '%', 'font': {'size': 42}},
        delta={'reference': 70, 'suffix': '%', 'font': {'size': 14}},
        title={'text': 'Visitas con Venta vs Total (Meta: 70%)', 'font': {'size': 13}},
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': '#2563eb'},
               'steps': [{'range': [0, 30], 'color': '#fee2e2'}, {'range': [30, 60], 'color': '#fef3c7'}, {'range': [60, 100], 'color': '#d1fae5'}],
               'threshold': {'line': {'color': '#dc2626', 'width': 3}, 'thickness': 0.8, 'value': 70}}
    ))
    fig.update_layout(paper_bgcolor='white', height=360, margin=dict(l=30, r=30, t=60, b=20))
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SECTION 4: TICKET
# ============================================================
st.markdown('<div class="section-title">🎟️ Análisis de Ticket Promedio</div>', unsafe_allow_html=True)

c4a, c4b = st.columns(2)

with c4a:
    st.markdown('<div class="chart-card"><h4>🎟️ Ticket Promedio por Mercaderista <span class="chart-tag">Barras</span></h4>', unsafe_allow_html=True)
    vt = v.groupby('MERCADERISTA', as_index=False).agg(total_val=('VALOR', 'sum'), lineas=('VALOR', 'count'))
    vt['ticket'] = vt['total_val'] / vt['lineas']
    vt = vt.sort_values('ticket', ascending=True)
    if not vt.empty:
        fig = px.bar(vt, y='MERCADERISTA', x='ticket', orientation='h',
                     text=vt['ticket'].apply(lambda x: f"${x:,.2f}"),
                     color='ticket', color_continuous_scale='Blues',
                     labels={'ticket': 'Ticket Promedio ($)', 'MERCADERISTA': ''})
        fig.update_layout(**base_layout(300), showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(tickfont=dict(size=10), gridcolor='#eee'))
        fig.update_traces(textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c4b:
    st.markdown('<div class="chart-card"><h4>🏪 Top 20 PDVs por Ticket <span class="chart-tag">Ranking</span></h4>', unsafe_allow_html=True)
    vp = v.groupby('PDV', as_index=False).agg(total_val=('VALOR', 'sum'), lineas=('VALOR', 'count'))
    vp['ticket'] = vp['total_val'] / vp['lineas']
    top20 = vp.sort_values('ticket', ascending=False).head(20).sort_values('ticket', ascending=True)
    if not top20.empty:
        fig = px.bar(top20, y='PDV', x='ticket', orientation='h',
                     text=top20['ticket'].apply(lambda x: f"${x:,.2f}"),
                     color='ticket', color_continuous_scale='Greens',
                     labels={'ticket': 'Ticket Promedio ($)', 'PDV': ''})
        fig.update_layout(**base_layout(max(340, len(top20)*18)), showlegend=False, coloraxis_showscale=False,
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(tickfont=dict(size=8), gridcolor='#eee'))
        fig.update_traces(textposition='outside', textfont_size=9)
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SECTION 5: COVERAGE
# ============================================================
st.markdown('<div class="section-title">🗺️ Análisis de Cobertura</div>', unsafe_allow_html=True)

c5a, c5b = st.columns(2)

with c5a:
    st.markdown('<div class="chart-card"><h4>📊 PDVs Asignados vs Visitados <span class="chart-tag">Comparativo</span></h4>', unsafe_allow_html=True)
    pdv_asig = pdv_master.groupby('Provincia', as_index=False).agg(asignados=('Nombre', 'nunique'))
    pdv_vis = imp.groupby('PROVINCIA', as_index=False).agg(visitados=('PDV', 'nunique')) if 'PROVINCIA' in imp.columns and len(imp) > 0 else pd.DataFrame()
    if not pdv_vis.empty:
        pdv_vis.rename(columns={'PROVINCIA': 'Provincia'}, inplace=True)
        cob = pdv_asig.merge(pdv_vis, on='Provincia', how='left').fillna(0)
        cob['visitados'] = cob['visitados'].astype(int)
        cob['%_cob'] = (cob['visitados'] / cob['asignados'] * 100).round(1)
        cob = cob.sort_values('asignados', ascending=True)
        fig = go.Figure()
        fig.add_trace(go.Bar(y=cob['Provincia'], x=cob['asignados'], name='Asignados', orientation='h',
                             marker_color='#93c5fd', text=cob['asignados'], textposition='auto', textfont_size=9))
        fig.add_trace(go.Bar(y=cob['Provincia'], x=cob['visitados'], name='Visitados', orientation='h',
                             marker_color='#2563eb',
                             text=cob.apply(lambda r: f"{int(r['visitados'])} ({r['%_cob']}%)", axis=1),
                             textposition='auto', textfont_size=9))
        fig.update_layout(**base_layout(max(320, len(cob)*30)), barmode='group',
                          legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
                          xaxis=dict(gridcolor='#eee'), yaxis=dict(gridcolor='#eee'))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

with c5b:
    st.markdown('<div class="chart-card"><h4>🔥 Cobertura por Mercaderista × Provincia <span class="chart-tag">Heatmap</span></h4>', unsafe_allow_html=True)
    cob_heat = imp.groupby(['MERCADERISTA', 'PROVINCIA'], as_index=False).agg(pdvs=('PDV', 'nunique'))
    if not cob_heat.empty:
        pivot = cob_heat.pivot_table(index='MERCADERISTA', columns='PROVINCIA', values='pdvs', fill_value=0)
        fig = px.imshow(pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
                        color_continuous_scale='Blues', text_auto=True,
                        labels=dict(x='Provincia', y='Mercaderista', color='PDVs'), aspect='auto')
        fig.update_layout(plot_bgcolor='white', paper_bgcolor='white', font=dict(size=11),
                          margin=dict(l=20, r=20, t=20, b=20), height=max(320, len(pivot)*55),
                          yaxis=dict(tickfont=dict(size=9)), xaxis=dict(tickfont=dict(size=9), side='top'))
        st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SECTION 6: MAP
# ============================================================
st.markdown('<div class="section-title">🌎 Mapa de Cobertura y Ventas</div>', unsafe_allow_html=True)
st.markdown('<div class="chart-card"><h4>🌎 Mapa Geográfico de Puntos de Venta <span class="chart-tag">Interactivo</span></h4>', unsafe_allow_html=True)

pdv_geo = pdv_master[['Nombre', 'Latitude', 'Longitude', 'Provincia', 'Ciudad', 'Categoria']].copy()
pdv_geo['Latitude'] = pd.to_numeric(pdv_geo['Latitude'], errors='coerce')
pdv_geo['Longitude'] = pd.to_numeric(pdv_geo['Longitude'], errors='coerce')
pdv_geo = pdv_geo.dropna(subset=['Latitude', 'Longitude']).rename(columns={'Nombre': 'PDV'})
sales_by_pdv = v.groupby('PDV', as_index=False)['VALOR'].sum()
visited_set = set(imp['PDV'].unique())
pdv_map = pdv_geo.merge(sales_by_pdv, on='PDV', how='left')
pdv_map['VALOR'] = pd.to_numeric(pdv_map['VALOR'], errors='coerce').fillna(0)
pdv_map['Estado'] = pdv_map.apply(lambda r: '🟢 Con Venta' if r['VALOR'] > 0 else ('🔵 Visitado' if r['PDV'] in visited_set else '⚪ No Visitado'), axis=1)
pdv_map['bubble'] = pdv_map['VALOR'].apply(lambda x: max(float(x), 3.0))

if not pdv_map.empty:
    fig = px.scatter_mapbox(pdv_map, lat='Latitude', lon='Longitude', size='bubble', color='Estado',
                            color_discrete_map={'🟢 Con Venta': '#059669', '🔵 Visitado': '#2563eb', '⚪ No Visitado': '#d1d5db'},
                            hover_name='PDV', hover_data={'VALOR': ':$.2f', 'Provincia': True, 'Ciudad': True, 'bubble': False},
                            size_max=20, zoom=7, mapbox_style='carto-positron',
                            category_orders={'Estado': ['🟢 Con Venta', '🔵 Visitado', '⚪ No Visitado']})
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=520,
                      legend=dict(orientation='h', yanchor='bottom', y=1.01, xanchor='center', x=0.5, font=dict(size=11)))
    st.plotly_chart(fig, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# ============================================================
# SECTION 7: TABLES
# ============================================================
st.markdown('<div class="section-title">📋 Tablas de Detalle</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["💰 Ventas por Merc/Mes", "📊 Resumen por PDV", "⏱️ Detalle Visitas"])

with tab1:
    pivot_v = v.pivot_table(index='MERCADERISTA', columns='MES_LABEL', values='VALOR',
                            aggfunc='sum', fill_value=0, margins=True, margins_name='TOTAL')
    st.dataframe(pivot_v.style.format("${:,.2f}").background_gradient(cmap='Blues', axis=1), use_container_width=True, height=250)

with tab2:
    pdv_sum = v.groupby('PDV', as_index=False).agg(
        ventas=('VALOR', 'sum'), unidades=('CANTIDAD', 'sum'),
        marcas=('MARCA', 'nunique'), lineas=('VALOR', 'count')
    ).sort_values('ventas', ascending=False)
    pdv_sum['ticket'] = pdv_sum['ventas'] / pdv_sum['lineas']
    pdv_sum.columns = ['PDV', 'Ventas ($)', 'Unidades', '# Marcas', 'Líneas', 'Ticket ($)']
    st.dataframe(pdv_sum.style.format({'Ventas ($)': '${:,.2f}', 'Unidades': '{:,.0f}', 'Ticket ($)': '${:,.2f}'})
                 .background_gradient(subset=['Ventas ($)'], cmap='Greens'), use_container_width=True, height=400)

with tab3:
    imp_det = imp[['PDV', 'MERCADERISTA', 'FECHA', 'HORA', 'HORA SALIDA', 'DURACION_MIN', 'CIUDAD', 'PROVINCIA', 'ZONA']].copy()
    imp_det = imp_det.dropna(subset=['DURACION_MIN']).sort_values('FECHA', ascending=False)
    imp_det['DURACION_MIN'] = imp_det['DURACION_MIN'].round(1)
    imp_det.columns = ['PDV', 'Mercaderista', 'Fecha', 'Entrada', 'Salida', 'Duración (min)', 'Ciudad', 'Provincia', 'Zona']
    st.dataframe(imp_det, use_container_width=True, height=400)

st.markdown("""
<div class="footer">
    ⭐ ESTRELLA Vendedor TAT – Tablero de Control<br>
    Para actualizar: reemplaza el archivo <code>data.xlsx</code> en el repositorio de GitHub
</div>
""", unsafe_allow_html=True)
