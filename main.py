import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit import download_button
import io
import plotly.graph_objects as go

# Función básica para calcular ROA
def calcularROAunMES(df):
    # Calcular los Ingresos Totales
    ingresos_totales = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
    # Calcular los Gastos Totales
    gastos_totales = df[df["TIPO"] == 4]["PADRE JULIAN LORENTE LTDA"].sum()
    # Calcular los Activos
    activos = df[df["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
    # Calcular la Utilidad neta
    utilidad_neta = ingresos_totales - gastos_totales
    return ingresos_totales, gastos_totales, utilidad_neta

# Función básica para calcular ROA de dos meses
def calcularROAMESES(mes, df, mes1, df1):
    resultados = {
        'Mes': [],
        'Ingresos Totales': [],
        'Gastos Totales': [],
        'Utilidad Neta': [],
        'Activo Promedio': [],
    }
    ingresos_totales = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
    gastos_totales = df[df["TIPO"] == 4]["PADRE JULIAN LORENTE LTDA"].sum()
    activos = df[df["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
    utilidad_neta1 = ingresos_totales - gastos_totales

    resultados['Mes'].append(mes)
    resultados['Ingresos Totales'].append(ingresos_totales)
    resultados['Gastos Totales'].append(gastos_totales)
    resultados['Activo Promedio'].append(activos)
    resultados['Utilidad Neta'].append(utilidad_neta1)

    ingresos_totales1 = df1[df1["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
    gastos_totales1 = df1[df1["TIPO"] == 4]["PADRE JULIAN LORENTE LTDA"].sum()
    activos1 = df1[df1["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
    utilidad_neta2 = ingresos_totales1 - gastos_totales1
    resultados['Mes'].append(mes1)
    resultados['Ingresos Totales'].append(ingresos_totales1)
    resultados['Gastos Totales'].append(gastos_totales1)
    resultados['Activo Promedio'].append(activos1)
    resultados['Utilidad Neta'].append(utilidad_neta2)

    utilidad_neta = utilidad_neta1 + utilidad_neta2
    activo_promedio = (activos + activos1) / 2
    ROA = (utilidad_neta / activo_promedio) * 100

    return pd.DataFrame(resultados), ingresos_totales1, gastos_totales1, utilidad_neta, ROA

# Función básica para calcular Eficiencia en Gasto Operativo
def calcularEficienciaGastoOperativo(df):
    ingresos_totales = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
    gastos_operativos = df[df["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
    eficiencia = ((ingresos_totales - gastos_operativos) / ingresos_totales) * 100
    return eficiencia, ingresos_totales, gastos_operativos

# Función básica para calcular Solvencia Patrimonial
def calcularSolvenciaPatrimonial(df):
    patrimonio = df[df["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum()
    activo_total = df[df["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
    solvencia = (patrimonio / activo_total) * 100
    return solvencia, patrimonio, activo_total

# Función básica para graficar
def crearGraficoBasico(datos, titulo):
    fig = px.bar(datos, x='Categoria', y='Valor', title=titulo)
    return fig

# Cargar datos básicos
dfs = {
'Enero' : pd.read_csv('CSV/ENERO.csv'),
'Febrero' : pd.read_csv('CSV/FEBRERO.csv'),
'Marzo' : pd.read_csv('CSV/MARZO.csv'),
'Abril' : pd.read_csv('CSV/ABRIL.csv'),
'Mayo' : pd.read_csv('CSV/MAYO.csv'),
'Junio' : pd.read_csv('CSV/JUNIO.csv'),
'Julio' : pd.read_csv('CSV/JULIO.csv'),
'Agosto' : pd.read_csv('CSV/AGOSTO.csv'),
'Septiembre' : pd.read_csv('CSV/SEPTIEMBRE.csv'),
'Octubre' : pd.read_csv('CSV/OCTUBRE.csv'),
'Noviembre' : pd.read_csv('CSV/NOVIEMBRE.csv'),
}

# Limpiar datos básicos
for df in dfs.values():
    if 'Unnamed: 5' in df.columns:
        df.drop('Unnamed: 5', axis=1, inplace=True)
    df["PADRE JULIAN LORENTE LTDA"] = df["PADRE JULIAN LORENTE LTDA"].astype(str).str.replace(',', '').astype(float)

# Valores fijos originales
roa = 3.73
eficiencia_gasto_operativo = 8.75
solvencia_patrimonial = 40.56

st.header("DASHBOARD")
# Crear la "tarjeta" de indicador básica
def mostrar_indicador(titulo, valor, unidad='%'):
    st.markdown(f"""
    <div style='padding: 20px; border-radius: 10px; background-color: #ffcc00; margin: 10px 0; text-align: center;'>
        <h4>{titulo}</h4>
        <h2>{valor}{unidad}</h2>
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    mostrar_indicador("ROA", roa)
with col2:
    mostrar_indicador("Eficiencia en Gasto Operativo", eficiencia_gasto_operativo)
with col3:
    mostrar_indicador("Solvencia Patrimonial", solvencia_patrimonial)

# Gráfico principal de resumen - usando datos reales del último mes disponible
st.subheader("📊 Resumen Financiero - Último Mes")
ultimo_mes = 'Noviembre'  # Último mes disponible
df_resumen = dfs[ultimo_mes]

# Calcular valores reales para el resumen
ingresos_resumen = df_resumen[df_resumen["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
gastos_resumen = df_resumen[df_resumen["TIPO"] == 4]["PADRE JULIAN LORENTE LTDA"].sum()
utilidad_resumen = ingresos_resumen - gastos_resumen

# Mostrar métricas principales
col_metricas, col_grafico = st.columns([1, 2])

with col_metricas:
    st.metric("**Ingresos Totales**", f"${ingresos_resumen:,.2f}")
    st.metric("**Gastos Totales**", f"${gastos_resumen:,.2f}")
    st.metric("**Utilidad Neta**", f"${utilidad_resumen:,.2f}")
    # Calcular margen de utilidad
    margen = (utilidad_resumen / ingresos_resumen * 100) if ingresos_resumen > 0 else 0
    st.metric("**Margen de Utilidad**", f"{margen:.2f}%")

with col_grafico:
    # Gráfico de barras con formato en millones para mejor visualización
    ingresos_millions = ingresos_resumen / 1_000_000
    gastos_millions = gastos_resumen / 1_000_000
    utilidad_millions = utilidad_resumen / 1_000_000
    
    datos_resumen = {
        'Categoría': ['Ingresos', 'Gastos', 'Utilidad'],
        'Valor (Millones)': [ingresos_millions, gastos_millions, utilidad_millions]
    }
    df_grafico_resumen = pd.DataFrame(datos_resumen)
    fig_resumen = px.bar(df_grafico_resumen, x='Categoría', y='Valor (Millones)',
                         title=f'Resumen Financiero - {ultimo_mes} (en Millones)',
                         color='Categoría',
                         color_discrete_sequence=['#4CAF50', '#F44336', '#2196F3'])
    fig_resumen.update_layout(showlegend=False, yaxis_title='Millones de $')
    fig_resumen.update_traces(texttemplate='%{y:.1f}M', textposition='outside')
    st.plotly_chart(fig_resumen)

# Sidebar básico
with st.sidebar:
    st.image('padre_julian.png', width=240)
    st.markdown("## Menú Principal")
    st.markdown("---")
    with st.expander("Ver Opciones"):
        seleccion_usuario = st.radio("Selecciona una opción:", ('Inicio', 'Análisis', 'Proyecciones'))

# Pestañas básicas
tab1, tab2, tab3 = st.tabs(["ROA", "Eficiencia en gasto Operativo", "Solvencia Patrimonial"])

with tab1:
    st.header("Rentabilidad sobre el activo (ROA)")

    # Mantener los selectores de mes como estaban
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        mes_inicio = st.selectbox("Seleccione el mes inicial:", list(dfs.keys()))
    with col2:
        mes_final = st.selectbox("Seleccione el mes final:", list(dfs.keys()))
    with col3:
        año = st.selectbox("Seleccione el año:", ['2022','2023'])

    if True:  # Siempre mostrar la comparación de dos meses

        if año == '2022':
            df_inicio = dfs[mes_inicio]
            df_final = dfs[mes_final]
        else:
            df_inicio = dfs[mes_inicio]
            df_final = dfs[mes_final]

        df_meses, ingresos, gastos, utilidad, roa_calc = calcularROAMESES(mes_inicio,df_inicio,mes_final, df_final)

        # Mostrar resultados principales
        col_resultados, col_grafico = st.columns([1, 2])

        with col_resultados:
            st.metric("**ROA Calculado**", f"{roa_calc:.2f}%")
            st.metric("**Utilidad Total**", f"${utilidad:,.2f}")
            st.metric("**Activo Promedio**", f"${(df_meses['Activo Promedio'].mean()):,.2f}")

        with col_grafico:
            # Gráfico de líneas para mostrar la evolución
            fig = px.line(df_meses, x='Mes', y=['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta'],
                         title=f'Evolución Financiera: {mes_inicio} vs {mes_final}',
                         markers=True,
                         color_discrete_sequence=['#4CAF50', '#F44336', '#2196F3'])
            fig.update_layout(yaxis_title='Monto ($)', xaxis_title='Mes')
            st.plotly_chart(fig)

        # Tabla de detalles (colapsable para no ocupar espacio)
        with st.expander("Ver detalles completos"):
            st.dataframe(df_meses)

# Gráfico de Evolución Financiera Anual (fuera de las pestañas)
st.markdown("---")
st.subheader("📈 Evolución Financiera Anual")

# Función para crear datos anuales
def crear_datos_evolucion_anual(dfs):
    meses = []
    ingresos_anuales = []
    gastos_anuales = []
    utilidad_anuales = []
    
    for mes, df in dfs.items():
        ingresos = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        gastos = df[df["TIPO"] == 4]["PADRE JULIAN LORENTE LTDA"].sum()
        utilidad = ingresos - gastos
        
        meses.append(mes)
        ingresos_anuales.append(ingresos / 1_000_000)  # Convertir a millones
        gastos_anuales.append(gastos / 1_000_000)
        utilidad_anuales.append(utilidad / 1_000_000)
    
    return {
        'Mes': meses,
        'Ingresos (Millones)': ingresos_anuales,
        'Gastos (Millones)': gastos_anuales,
        'Utilidad (Millones)': utilidad_anuales
    }

# Crear datos para el gráfico anual
datos_anuales = crear_datos_evolucion_anual(dfs)
df_evolucion = pd.DataFrame(datos_anuales)

# Gráfico de líneas de evolución anual
fig_evolucion = px.line(df_evolucion, x='Mes', 
                       y=['Ingresos (Millones)', 'Gastos (Millones)', 'Utilidad (Millones)'],
                       title='Evolución Financiera - Todo el Año (en Millones)',
                       markers=True,
                       color_discrete_sequence=['#4CAF50', '#F44336', '#2196F3'])
fig_evolucion.update_layout(
    yaxis_title='Millones de $',
    xaxis_title='Mes',
    xaxis={'categoryorder': 'array', 'categoryarray': list(dfs.keys())},
    height=500
)
fig_evolucion.update_traces(line=dict(width=3), marker=dict(size=8))
st.plotly_chart(fig_evolucion, use_container_width=True)

# Métricas resumen del año
col_resumen1, col_resumen2, col_resumen3, col_resumen4 = st.columns(4)

ingresos_total_año = sum(datos_anuales['Ingresos (Millones)'])
gastos_total_año = sum(datos_anuales['Gastos (Millones)'])
utilidad_total_año = sum(datos_anuales['Utilidad (Millones)'])
margen_promedio_año = (utilidad_total_año / ingresos_total_año * 100) if ingresos_total_año > 0 else 0

with col_resumen1:
    st.metric("**Ingresos Totales Año**", f"${ingresos_total_año:.1f}M")
with col_resumen2:
    st.metric("**Gastos Totales Año**", f"${gastos_total_año:.1f}M")
with col_resumen3:
    st.metric("**Utilidad Total Año**", f"${utilidad_total_año:.1f}M")
with col_resumen4:
    st.metric("**Margen Promedio**", f"{margen_promedio_año:.2f}%")

# Pestañas con funcionalidad básica
with tab2:
    st.header("Eficiencia en gasto operativo")

    # Selector de mes básico
    mes_seleccionado = st.selectbox("Selecciona un mes para calcular la eficiencia:", list(dfs.keys()))
    df_seleccionado = dfs[mes_seleccionado]

    # Calcular eficiencia
    eficiencia, ingresos, gastos = calcularEficienciaGastoOperativo(df_seleccionado)

    # Mostrar resultados principales
    col_metricas, col_grafico = st.columns([1, 2])

    with col_metricas:
        st.metric("**Eficiencia Operativa**", f"{eficiencia:.2f}%")
        st.metric("**Ingresos Totales**", f"${ingresos:,.2f}")
        st.metric("**Gastos Operativos**", f"${gastos:,.2f}")
        ahorro = ingresos - gastos
        st.metric("**Ahorro Generado**", f"${ahorro:,.2f}")

    with col_grafico:
        # Gráfico de composición: qué porcentaje representan los gastos operativos
        datos_composicion = {
            'Categoría': ['Gastos Operativos', 'Ingresos Restantes'],
            'Valor': [gastos, ahorro],
            'Tipo': ['Gasto', 'Beneficio']
        }
        df_composicion = pd.DataFrame(datos_composicion)
        fig_composicion = px.pie(df_composicion, values='Valor', names='Categoría',
                                title=f'Composición de Ingresos - {mes_seleccionado}',
                                color_discrete_sequence=['#F44336', '#4CAF50'])
        st.plotly_chart(fig_composicion)

with tab3:
    st.header("Solvencia Patrimonial")

    # Selector de mes básico
    mes_seleccionado_sol = st.selectbox("Selecciona un mes para calcular la solvencia:", list(dfs.keys()))
    df_seleccionado_sol = dfs[mes_seleccionado_sol]

    # Calcular solvencia
    solvencia, patrimonio, activo = calcularSolvenciaPatrimonial(df_seleccionado_sol)

    # Mostrar resultados principales
    col_metricas, col_grafico = st.columns([1, 2])

    with col_metricas:
        st.metric("**Solvencia Patrimonial**", f"{solvencia:.2f}%")
