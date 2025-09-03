import pandas as pd
import streamlit as st
import plotly.express as px
from streamlit import download_button
import io
import plotly.graph_objects as go
from functools import lru_cache
import os

# Cache para datos cargados
@st.cache_data
def cargar_datos_meses():
    """Carga bajo demanda los datos mensuales solo cuando se necesitan"""
    meses = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
             'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre']

    dfs = {}
    dfs2022 = {}

    for mes in meses:
        ruta_actual = f'CSV/{mes.upper()}.csv'
        ruta_2022 = f'CSV/2022/{mes}.csv'

        if os.path.exists(ruta_actual):
            dfs[mes] = pd.read_csv(ruta_actual)
        if os.path.exists(ruta_2022):
            dfs2022[mes] = pd.read_csv(ruta_2022)

    return dfs, dfs2022

# Función auxiliar para calcular métricas financieras básicas
def calcular_metricas_basicas(df, tipo_ingresos=5, tipo_gastos=4, tipo_activos=1, columna_activos="CODIGO_CONTABLE"):
    """
    Función auxiliar para calcular métricas financieras básicas.
    Evita duplicación de código en todas las funciones de cálculo.
    """
    try:
        # Ingresos totales
        ingresos = df[df["TIPO"] == tipo_ingresos]["PADRE JULIAN LORENTE LTDA"].sum()

        # Gastos totales
        gastos = df[df["TIPO"] == tipo_gastos]["PADRE JULIAN LORENTE LTDA"].sum()

        # Activos totales
        activos = df[df[columna_activos] == tipo_activos]["PADRE JULIAN LORENTE LTDA"].sum()

        # Utilidad neta
        utilidad_neta = ingresos - gastos

        return {
            'ingresos': ingresos,
            'gastos': gastos,
            'activos': activos,
            'utilidad_neta': utilidad_neta
        }
    except Exception as e:
        st.error(f"Error al calcular métricas básicas: {e}")
        return {
            'ingresos': 0,
            'gastos': 0,
            'activos': 1,  # Evitar división por cero
            'utilidad_neta': 0
        }

# Función auxiliar para calcular métricas de eficiencia
def calcular_metricas_eficiencia(df, tipo_ingresos=5, tipo_gastos_operativos=45):
    """
    Función auxiliar para calcular métricas de eficiencia en gasto operativo.
    """
    try:
        # Ingresos totales
        ingresos = df[df["TIPO"] == tipo_ingresos]["PADRE JULIAN LORENTE LTDA"].sum()

        # Gastos operativos
        gastos_operativos = df[df["CODIGO_CONTABLE"] == tipo_gastos_operativos]["PADRE JULIAN LORENTE LTDA"].sum()

        # Eficiencia en gasto operativo
        eficiencia = (ingresos - gastos_operativos) / ingresos if ingresos != 0 else 0

        return {
            'ingresos': ingresos,
            'gastos_operativos': gastos_operativos,
            'eficiencia': eficiencia
        }
    except Exception as e:
        st.error(f"Error al calcular métricas de eficiencia: {e}")
        return {
            'ingresos': 0,
            'gastos_operativos': 0,
            'eficiencia': 0
        }

# Función auxiliar para calcular métricas de solvencia
def calcular_metricas_solvencia(df, tipo_patrimonio=3, tipo_activos=1):
    """
    Función auxiliar para calcular métricas de solvencia patrimonial.
    """
    try:
        # Patrimonio
        patrimonio = df[df["TIPO"] == tipo_patrimonio]["PADRE JULIAN LORENTE LTDA"].sum()

        # Activos totales
        activos_total = df[df["CODIGO_CONTABLE"] == tipo_activos]["PADRE JULIAN LORENTE LTDA"].sum()

        # Solvencia patrimonial
        solvencia = (patrimonio / activos_total) * 100 if activos_total != 0 else 0

        return {
            'patrimonio': patrimonio,
            'activos_total': activos_total,
            'solvencia': solvencia
        }
    except Exception as e:
        st.error(f"Error al calcular métricas de solvencia: {e}")
        return {
            'patrimonio': 0,
            'activos_total': 1,  # Evitar división por cero
            'solvencia': 0
        }

# Función para validar datos financieros
def validar_datos_financieros(df, nombre_archivo=""):
    """
    Valida la integridad de los datos financieros y reporta problemas.
    """
    errores = []
    advertencias = []

    try:
        # Verificar columnas requeridas
        columnas_requeridas = ['CODIGO_CONTABLE', 'TIPO', 'PADRE JULIAN LORENTE LTDA']
        for col in columnas_requeridas:
            if col not in df.columns:
                errores.append(f"❌ Columna requerida faltante: {col}")

        if errores:
            return False, errores, []

        # Verificar tipos de datos
        try:
            df_copy = df.copy()
            df_copy["PADRE JULIAN LORENTE LTDA"] = pd.to_numeric(df_copy["PADRE JULIAN LORENTE LTDA"], errors='coerce')
            if df_copy["PADRE JULIAN LORENTE LTDA"].isna().any():
                advertencias.append("⚠️ Algunos valores monetarios no pudieron convertirse a números")
        except Exception as e:
            errores.append(f"❌ Error convirtiendo valores monetarios: {e}")

        # Verificar rangos de datos razonables
        valores_monetarios = pd.to_numeric(df["PADRE JULIAN LORENTE LTDA"], errors='coerce')
        valores_monetarios = valores_monetarios.dropna()

        if len(valores_monetarios) == 0:
            errores.append("❌ No hay valores monetarios válidos en el archivo")
        else:
            # Verificar valores extremos
            valores_extremos = valores_monetarios[abs(valores_monetarios) > 1e12]  # Más de 1 billón
            if len(valores_extremos) > 0:
                advertencias.append(f"⚠️ {len(valores_extremos)} valores monetarios parecen extremos (> 1 billón)")

        # Verificar tipos de cuenta válidos
        tipos_validos = [1, 2, 3, 4, 5]
        tipos_presentes = df['TIPO'].unique()
        tipos_invalidos = [t for t in tipos_presentes if t not in tipos_validos and pd.notna(t)]
        if tipos_invalidos:
            advertencias.append(f"⚠️ Tipos de cuenta no estándar encontrados: {tipos_invalidos}")

        return len(errores) == 0, errores, advertencias

    except Exception as e:
        errores.append(f"❌ Error general en validación: {e}")
        return False, errores, advertencias

# Función genérica para calcular métricas múltiples meses
def calcular_metricas_multiples(funcion_calculo, dfs_lista, nombres_meses):
    """
    Función genérica para calcular métricas en múltiples meses.
    Evita duplicación de código en funciones de 2, 3 o más meses.

    Args:
        funcion_calculo: Función de cálculo a aplicar (ej: calcular_metricas_basicas)
        dfs_lista: Lista de DataFrames a procesar
        nombres_meses: Lista de nombres de meses correspondientes

    Returns:
        dict: Resultados consolidados
    """
    resultados = {
        'meses': [],
        'metricas': []
    }

    for df, nombre_mes in zip(dfs_lista, nombres_meses):
        metricas = funcion_calculo(df)
        resultados['meses'].append(nombre_mes)
        resultados['metricas'].append(metricas)

    return resultados

# Función para calcular indicadores principales dinámicamente
def calcular_indicadores_principales(dfs, mes_actual='Enero'):
    """
    Calcula los indicadores principales (ROA, Eficiencia, Solvencia) basados en datos reales.
    Esta función reemplaza los valores hardcodeados.
    """
    try:
        df = dfs[mes_actual]

        # Calcular métricas básicas para ROA
        metricas_basicas = calcular_metricas_basicas(df)
        roa = (metricas_basicas['utilidad_neta'] / metricas_basicas['activos']) * 100 if metricas_basicas['activos'] != 0 else 0

        # Calcular eficiencia operativa
        metricas_eficiencia = calcular_metricas_eficiencia(df)
        eficiencia = metricas_eficiencia['eficiencia'] * 100  # Convertir a porcentaje

        # Calcular solvencia patrimonial
        metricas_solvencia = calcular_metricas_solvencia(df)
        solvencia = metricas_solvencia['solvencia']

        return {
            'roa': roa,
            'eficiencia': eficiencia,
            'solvencia': solvencia,
            'mes_actual': mes_actual
        }
    except Exception as e:
        st.error(f"Error calculando indicadores principales: {e}")
        return {
            'roa': 0.0,
            'eficiencia': 0.0,
            'solvencia': 0.0,
            'mes_actual': mes_actual
        }

def calcularROAunMES(df):
    """
    Calcula ROA para un solo mes usando la función auxiliar refactorizada.
    """
    metricas = calcular_metricas_basicas(df)
    roa = (metricas['utilidad_neta'] / metricas['activos']) * 100 if metricas['activos'] != 0 else 0
    return metricas['ingresos'], metricas['gastos'], metricas['utilidad_neta']

def calcularROAMESES(mes, df, mes1, df1):
    """
    Calcula ROA para dos meses usando la función auxiliar refactorizada.
    """
    resultados = {
        'Mes': [],
        'Ingresos Totales': [],
        'Gastos Totales': [],
        'Utilidad Neta': [],
        'Activo Promedio': [],
    }

    # Calcular métricas para ambos meses usando la función auxiliar
    metricas_mes1 = calcular_metricas_basicas(df)
    metricas_mes2 = calcular_metricas_basicas(df1)

    # Agregar resultados del primer mes
    resultados['Mes'].append(mes)
    resultados['Ingresos Totales'].append(metricas_mes1['ingresos'])
    resultados['Gastos Totales'].append(metricas_mes1['gastos'])
    resultados['Activo Promedio'].append(metricas_mes1['activos'])
    resultados['Utilidad Neta'].append(metricas_mes1['utilidad_neta'])

    # Agregar resultados del segundo mes
    resultados['Mes'].append(mes1)
    resultados['Ingresos Totales'].append(metricas_mes2['ingresos'])
    resultados['Gastos Totales'].append(metricas_mes2['gastos'])
    resultados['Activo Promedio'].append(metricas_mes2['activos'])
    resultados['Utilidad Neta'].append(metricas_mes2['utilidad_neta'])

    # Calcular ROA combinado
    utilidad_neta_total = metricas_mes1['utilidad_neta'] + metricas_mes2['utilidad_neta']
    activo_promedio = (metricas_mes1['activos'] + metricas_mes2['activos']) / 2
    roa = (utilidad_neta_total / activo_promedio) * 100 if activo_promedio != 0 else 0

    return pd.DataFrame(resultados), metricas_mes2['ingresos'], metricas_mes2['gastos'], utilidad_neta_total, roa
def calcularROATRIMESTRE(mes, df, mes1, df1, mes2, df2):
    """
    Calcula ROA para trimestre usando la función auxiliar refactorizada.
    """
    resultados_roa = {
        'Mes': [],
        'ROA': [],
    }

    resultados = {
        'Mes': [],
        'Ingresos Totales': [],
        'Gastos Totales': [],
        'Utilidad Neta': [],
        'Activo Promedio': [],
    }

    # Calcular métricas para los tres meses usando la función auxiliar
    dfs_meses = [df, df1, df2]
    meses_nombres = [mes, mes1, mes2]

    utilidad_neta_total = 0
    activos_totales = []

    for i, (df_mes, nombre_mes) in enumerate(zip(dfs_meses, meses_nombres)):
        metricas = calcular_metricas_basicas(df_mes)
        roa_mes = (metricas['utilidad_neta'] / metricas['activos']) * 100 if metricas['activos'] != 0 else 0

        # Agregar a resultados generales
        resultados['Mes'].append(nombre_mes)
        resultados['Ingresos Totales'].append(metricas['ingresos'])
        resultados['Gastos Totales'].append(metricas['gastos'])
        resultados['Activo Promedio'].append(metricas['activos'])
        resultados['Utilidad Neta'].append(metricas['utilidad_neta'])

        # Agregar a resultados ROA
        resultados_roa['Mes'].append(nombre_mes)
        resultados_roa['ROA'].append(roa_mes)

        utilidad_neta_total += metricas['utilidad_neta']
        activos_totales.append(metricas['activos'])

    # Calcular ROA trimestral
    activo_promedio = sum(activos_totales) / len(activos_totales)
    roa_trimestral = (utilidad_neta_total / activo_promedio) * 100 if activo_promedio != 0 else 0

    # Obtener métricas del último mes para compatibilidad con código existente
    metricas_ultimo_mes = calcular_metricas_basicas(df2)

    return (pd.DataFrame(resultados),
            pd.DataFrame(resultados_roa),
            metricas_ultimo_mes['ingresos'],
            metricas_ultimo_mes['gastos'],
            utilidad_neta_total,
            roa_trimestral)
def calcularROAAnual(dfs):
    """
    Calcula ROA anual usando la función auxiliar refactorizada.
    """
    resultados = {
        'Mes': [],
        'Ingresos Totales': [],
        'Gastos Totales': [],
        'Utilidad Neta': [],
        'Activo Promedio': [],
        'ROA': []
    }

    # Inicializar acumuladores
    ingresos_totales_anuales = 0
    gastos_totales_anuales = 0
    utilidad_neta_total = 0
    activos_totales = []

    # Procesar cada mes usando la función auxiliar
    for mes, df in dfs.items():
        # Para ROA anual usamos GRUPO == 1 para activos (diferente de las funciones mensuales)
        metricas = calcular_metricas_basicas(df, columna_activos="GRUPO")
        roa = (metricas['utilidad_neta'] / metricas['activos']) * 100 if metricas['activos'] != 0 else 0

        # Agregar resultados mensuales
        resultados['Mes'].append(mes)
        resultados['Ingresos Totales'].append(metricas['ingresos'])
        resultados['Gastos Totales'].append(metricas['gastos'])
        resultados['Utilidad Neta'].append(metricas['utilidad_neta'])
        resultados['Activo Promedio'].append(metricas['activos'])
        resultados['ROA'].append(roa)

        # Acumular totales
        ingresos_totales_anuales += metricas['ingresos']
        gastos_totales_anuales += metricas['gastos']
        utilidad_neta_total += metricas['utilidad_neta']
        activos_totales.append(metricas['activos'])

    # Calcular promedios y totales anuales
    num_meses = len(dfs)
    utilidad_neta_anual = ingresos_totales_anuales - gastos_totales_anuales
    activo_promedio_anual = sum(activos_totales) / num_meses if num_meses > 0 else 0

    # Calcular ROA anual (ajustado por el número de meses)
    ROA_anual = (utilidad_neta_anual / activo_promedio_anual) * 100 if activo_promedio_anual != 0 else 0

    return (pd.DataFrame(resultados),
            ingresos_totales_anuales,
            gastos_totales_anuales,
            utilidad_neta_anual,
            activo_promedio_anual,
            ROA_anual)
def crear_grafico(datos, titulo,resultados_df):
    fig = px.bar(datos, x='Categoria', y='Valor', title=titulo)
    fig.update_layout(xaxis={'categoryorder':'total descending'})

    # Pai
    pai = px.pie(resultados_df, names='Mes', values='ROA', title='ROA Mensuales',
                 color_discrete_sequence=['#1f77b4', '#ff7f0e', '#d62728'])

    return fig,pai

def  graficoMes(resultados_df,categoria):
    # Función para graficar
    fig2 = px.bar(resultados_df, x='Mes', y=categoria, title=f'{categoria} por Mes',color = categoria)
    return fig2

def crear_graficas_ROA(ingresos_totales, gastos_totales, utilidad_neta, ROA):
    # Creamos un DataFrame con los resultados para facilitar la graficación
    data = {
        'Categoría': ['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta'],
        'Valor': [ingresos_totales, gastos_totales, utilidad_neta]
    }
    resultados_df = pd.DataFrame(data)

    # Gráfico de barras para ingresos y gastos
    fig_bar = px.bar(resultados_df, x='Categoría', y='Valor', title='Ingresos y Gastos de dos meses',color= 'Valor')

    # Gráfico de ROA
    fig_roa = px.bar(x=['ROA'], y=[ROA], title='ROA de dos meses', labels={'y': 'ROA %', 'x': ''})
    fig_roa.update_layout(showlegend=False)

    return fig_bar, fig_roa


def calcularSolvenciaPatrimonialUnMes(df, nombre_mes):
    patrimonio = df[df["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum()
    activo_total = df[df["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
    solvencia_patrimonial = (patrimonio / activo_total) * 100

    # Crear un diccionario con los resultados
    resultados = {
        'Mes': nombre_mes,
        'Patrimonio': patrimonio,
        'Activo Total': activo_total,
        'Solvencia Patrimonial (%)': solvencia_patrimonial
    }

    # Convertir el diccionario en DataFrame
    resultados_df = pd.DataFrame([resultados])
    return resultados_df


def calcularSolvenciaPatrimonialDosMeses(df1, df2, mes1, mes2):
    resultados = {
        'Mes': [],
        'Patrimonio': [],
        'Activo Total': [],
        'Solvencia Patrimonial (%)': []
    }

    for df, mes in zip([df1, df2], [mes1, mes2]):
        patrimonio = df[df["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum()
        activo_total = df[df["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
        solvencia_patrimonial = (patrimonio / activo_total) * 100

        resultados['Mes'].append(mes)
        resultados['Patrimonio'].append(patrimonio)
        resultados['Activo Total'].append(activo_total)
        resultados['Solvencia Patrimonial (%)'].append(solvencia_patrimonial)

    resultados_df = pd.DataFrame(resultados)
    return resultados_df,solvencia_patrimonial,patrimonio,activo_total


def calcularSolvenciaPatrimonialTrimestre(df1, df2, df3):
    patrimonio = (df1[df1["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum() +
                  df2[df2["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum() +
                  df3[df3["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum()) / 3
    activo_total = (df1[df1["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum() +
                    df2[df2["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum() +
                    df3[df3["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()) / 3

    solvencia_patrimonial = (patrimonio / activo_total) * 100  # Porcentaje
    return solvencia_patrimonial


def calcularSolvenciaPatrimonialAnual(dfs):
    resultados_solvencia = {
        'Mes': [],
        'Patrimonio Promedio': [],
        'Activo Total Promedio': [],
        'Solvencia Patrimonial': [],
    }
    # Suponiendo que 'dfs' es un diccionario de dataframes con las claves siendo los meses del año

    patrimonio_total = 0
    activo_total_promedio = 0

    # Sumar el patrimonio y el activo total de todos los meses para obtener el promedio
    for mes,df in dfs.items():
        patrimonio_total += df[df["TIPO"] == 3]["PADRE JULIAN LORENTE LTDA"].sum()
        activo_total_promedio += df[df["CODIGO_CONTABLE"] == 1]["PADRE JULIAN LORENTE LTDA"].sum()
        solvencia_patrimonial_mensual = (patrimonio_total/activo_total_promedio)*100
        resultados_solvencia['Mes'].append(mes)
        resultados_solvencia['Patrimonio Promedio'].append(patrimonio_total)
        resultados_solvencia['Activo Total Promedio'].append(activo_total_promedio)
        resultados_solvencia['Solvencia Patrimonial'].append(solvencia_patrimonial_mensual)

    # Calcular promedios
    patrimonio_promedio = patrimonio_total / len(dfs)
    activo_total_promedio /= len(dfs)
    solvencia_patrimonial_anual = (patrimonio_promedio / activo_total_promedio) * 100

    # Crear un diccionario con los resultados anuales
    resultados_anuales = {
        'Categoria': ['Patrimonio Promedio', 'Activo Total Promedio', 'Solvencia Patrimonial (%)'],
        'Valor': [patrimonio_promedio, activo_total_promedio, solvencia_patrimonial_anual]
    }

    # Convertir el diccionario en DataFrame
    resultados_anuales_df = pd.DataFrame(resultados_anuales)
    resultados_solvencia_df = pd.DataFrame(resultados_solvencia)
    return resultados_anuales_df,resultados_solvencia_df, solvencia_patrimonial_anual, patrimonio_promedio, activo_total_promedio


def crear_grafico_solvencia(datosPai, columna_valor, nombre_pie, Patrimonio, activo_total_promedio,
                            solvencia_patrimonial):
    data_solvencia = {
        'Categoría': ['Patrimonio', 'Activo Total', ],
        'Valor': [Patrimonio, activo_total_promedio,]
    }
    resultados_solvencia = pd.DataFrame(data_solvencia)

    # Gráfico de barras para visualizar la solvencia patrimonial
    fig_bar = px.bar(resultados_solvencia, x='Categoría', y='Valor', title='Patrimonio y Activo Total de dos meses',
                     color= 'Valor')

    # Gráfico de pastel para visualizar la distribución de la solvencia patrimonial por mes
    pai = px.pie(datosPai, names='Mes', values='Solvencia Patrimonial', title=f'Solvencia Patrimonial {nombre_pie}',
                 )

    return fig_bar, pai
def crear_grafico_solvencia_meses(datosPai, columna_valor, nombre_pie, Patrimonio, activo_total_promedio,
                            solvencia_patrimonial):
    data_solvencia = {
        'Categoría': ['Patrimonio', 'Activo Total', ],
        'Valor': [Patrimonio, activo_total_promedio,]
    }
    resultados_solvencia = pd.DataFrame(data_solvencia)

    # Gráfico de barras para visualizar la solvencia patrimonial
    fig_bar = px.bar(resultados_solvencia, x='Categoría', y='Valor', title='Patrimonio y Activo Total de dos meses',color='Valor')

    # Gráfico de pastel para visualizar la distribución de la solvencia patrimonial por mes
    pai = px.pie(datosPai, names='Mes', values='Solvencia Patrimonial (%)', title=f'Solvencia Patrimonial {nombre_pie}',
                 color_discrete_sequence=['#1f77b4', '#ff7f0e', '#d62728'])

    return fig_bar, pai
def grafico_solvencia_mes(resultados_df, columna_valor):
    # Gráfico de barras para visualizar la solvencia patrimonial por mes
    fig_mes = px.bar(resultados_df, x='Mes', y=columna_valor, title=f'Solvencia Patrimonial por Mes',
                     color=columna_valor)

    return fig_mes

def crear_graficas_solvencia(datos_meses, titulo_bar, titulo_pie):
    # Gráfico de barras para la solvencia patrimonial por mes
    fig_bar = px.bar(datos_meses, x='Mes', y='Solvencia Patrimonial (%)', title=titulo_bar,
                     color='Solvencia Patrimonial (%)')

    # Gráfico de pastel para la distribución porcentual de la solvencia patrimonial
    fig_pie = px.pie(datos_meses, names='Mes', values='Solvencia Patrimonial (%)', title=titulo_pie,color_discrete_sequence=['#1f77b4', '#ff7f0e', '#d62728'])

    return fig_bar, fig_pie

def crear_grafico_anillo(df, titulo, columna_valor, columna_nombre):
    # Crear un gráfico de anillo (o 'donut') con Plotly Express
    fig = px.pie(df, values=columna_valor, names=columna_nombre, hole=0.7, title=titulo,color_discrete_sequence=['#1f77b4', '#ff7f0e', '#d62728'])

    # Personalizar el gráfico para que se parezca al de la imagen
    fig.update_traces(textinfo='none')  # Ocultar el texto dentro de las porciones
    fig.update_layout(
        showlegend=False,  # Ocultar la leyenda
        annotations=[
            dict(text=f'{df[columna_valor].mean():.2f}%', x=0.5, y=0.5, font_size=20, showarrow=False),
            dict(text='Promedio ROA', x=0.5, y=0.45, font_size=15, showarrow=False)
        ],
        margin=dict(t=0, b=0, l=15, r=0),  # Eliminar márgenes
        autosize=False, width=300, height=300
    )

    return fig
# Función para limpiar y procesar datos
def procesar_dataframe(df):
    """Limpia y procesa un DataFrame de datos financieros"""
    try:
        # Eliminar columnas no deseadas
        if 'Unnamed: 5' in df.columns:
            df = df.drop('Unnamed: 5', axis=1)

        # Convertir valores monetarios
        df["PADRE JULIAN LORENTE LTDA"] = (
            df["PADRE JULIAN LORENTE LTDA"]
            .astype(str)
            .str.replace(',', '')
            .astype(float)
        )
        return df
    except Exception as e:
        st.error(f"Error procesando DataFrame: {e}")
        return df

# Función para agregar fechas a los DataFrames
def agregar_fechas_a_dfs(dfs, año=2023):
    """Agrega fechas a los DataFrames mensuales"""
    fechas = {
        'Enero': f'{año}-01-01',
        'Febrero': f'{año}-02-01',
        'Marzo': f'{año}-03-01',
        'Abril': f'{año}-04-01',
        'Mayo': f'{año}-05-01',
        'Junio': f'{año}-06-01',
        'Julio': f'{año}-07-01',
        'Agosto': f'{año}-08-01',
        'Septiembre': f'{año}-09-01',
        'Octubre': f'{año}-10-01',
        'Noviembre': f'{año}-11-01',
    }

    for mes, df in dfs.items():
        if mes in fechas:
            df['Fecha'] = pd.to_datetime(fechas[mes])

    return dfs

# Cargar datos bajo demanda con caché
@st.cache_data
def cargar_y_procesar_datos():
    """Carga y procesa todos los datos financieros con caché para mejor rendimiento"""
    dfs, dfs2022 = cargar_datos_meses()

    # Procesar datos (limpiar y convertir tipos)
    dfs = {mes: procesar_dataframe(df) for mes, df in dfs.items()}
    dfs2022 = {mes: procesar_dataframe(df) for mes, df in dfs2022.items()}

    # Agregar fechas
    dfs = agregar_fechas_a_dfs(dfs, 2023)
    dfs2022 = agregar_fechas_a_dfs(dfs2022, 2022)

    return dfs, dfs2022

# Cargar datos procesados
dfs, dfs2022 = cargar_y_procesar_datos()

# Validar calidad de datos
def validar_calidad_datos():
    """Valida la calidad de todos los archivos de datos cargados"""
    resultados_validacion = {
        'archivos_validos': [],
        'archivos_con_errores': [],
        'archivos_con_advertencias': [],
        'total_archivos': 0
    }

    # Validar archivos principales (2023)
    for mes, df in dfs.items():
        valido, errores, advertencias = validar_datos_financieros(df, f"{mes}_2023.csv")
        resultados_validacion['total_archivos'] += 1

        if not valido:
            resultados_validacion['archivos_con_errores'].append({
                'archivo': f"{mes}_2023.csv",
                'errores': errores,
                'advertencias': advertencias
            })
        elif advertencias:
            resultados_validacion['archivos_con_advertencias'].append({
                'archivo': f"{mes}_2023.csv",
                'advertencias': advertencias
            })
        else:
            resultados_validacion['archivos_validos'].append(f"{mes}_2023.csv")

    # Validar archivos de 2022
    for mes, df in dfs2022.items():
        valido, errores, advertencias = validar_datos_financieros(df, f"{mes}_2022.csv")
        resultados_validacion['total_archivos'] += 1

        if not valido:
            resultados_validacion['archivos_con_errores'].append({
                'archivo': f"{mes}_2022.csv",
                'errores': errores,
                'advertencias': advertencias
            })
        elif advertencias:
            resultados_validacion['archivos_con_advertencias'].append({
                'archivo': f"{mes}_2022.csv",
                'advertencias': advertencias
            })
        else:
            resultados_validacion['archivos_validos'].append(f"{mes}_2022.csv")

    return resultados_validacion

# Ejecutar validación de datos
validacion_datos = validar_calidad_datos()

# Paleta de colores para gráficos
colores = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b',
           '#e377c2', '#7f7f7f', '#bcbd22', '#17becf', '#9edae5', '#ffbb78']

# Selector de mes para indicadores principales
st.header("📊 DASHBOARD FINANCIERO - PADRE JULIAN LORENTE LTDA")
st.markdown("---")

# Selector interactivo del mes de referencia
meses_disponibles = list(dfs.keys())
mes_seleccionado = st.selectbox(
    "📅 Selecciona el mes de referencia para los indicadores principales:",
    meses_disponibles,
    index=meses_disponibles.index('Enero') if 'Enero' in meses_disponibles else 0,
    help="Los indicadores principales (ROA, Eficiencia, Solvencia) se calcularán basados en los datos de este mes."
)

# Calcular indicadores reales basados en datos del mes seleccionado
indicadores_reales = calcular_indicadores_principales(dfs, mes_actual=mes_seleccionado)

# Crear la "tarjeta" de indicador mejorada
def mostrar_indicador(titulo, valor, unidad='%', mes='', descripcion=''):
    """
    Muestra un indicador financiero con información detallada
    """
    # Colores según el rendimiento
    if titulo.startswith('ROA'):
        color_fondo = "#4CAF50" if valor >= 1.0 else "#FF9800" if valor >= 0 else "#F44336"
    elif titulo.startswith('Eficiencia'):
        color_fondo = "#4CAF50" if valor >= 10.0 else "#FF9800" if valor >= 5.0 else "#F44336"
    elif titulo.startswith('Solvencia'):
        color_fondo = "#4CAF50" if valor >= 30.0 else "#FF9800" if valor >= 15.0 else "#F44336"
    else:
        color_fondo = "#2196F3"

    info_mes = f"<p style='margin:5px 0; color: #666; font-size: 0.8em;'>Mes: {mes}</p>" if mes else ""
    info_desc = f"<p style='margin:5px 0; color: #666; font-size: 0.7em;'>{descripcion}</p>" if descripcion else ""

    st.markdown(f"""
            <div style='
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        color: white;
        background-color: {color_fondo};
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        text-align: center;
        transition: transform 0.3s ease-in-out;
        display: inline-block;
        width: 100%;
        border: 2px solid rgba(255,255,255,0.3);'>
                <h4 style="margin:0; color: white; font-weight: bold;">{titulo}</h4>
                <h2 style="margin:10px 0; color: white; font-size:2.5em; font-weight: bold;">{valor:.2f}{unidad}</h2>
                {info_mes}
                {info_desc}
            </div>
        """, unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    mostrar_indicador(
        "📈 ROA (Rentabilidad sobre Activos)",
        indicadores_reales['roa'],
        mes=indicadores_reales['mes_actual'],
        descripcion="Eficiencia en generar utilidades con activos disponibles"
    )

with col2:
    mostrar_indicador(
        "⚡ Eficiencia Operativa",
        indicadores_reales['eficiencia'],
        unidad='%',
        mes=indicadores_reales['mes_actual'],
        descripcion="Porcentaje de ingresos restantes después de gastos operativos"
    )

with col3:
    mostrar_indicador(
        "🛡️ Solvencia Patrimonial",
        indicadores_reales['solvencia'],
        unidad='%',
        mes=indicadores_reales['mes_actual'],
        descripcion="Capacidad para cubrir obligaciones con patrimonio"
    )

# Información adicional
st.markdown("---")
col_info1, col_info2 = st.columns(2)

with col_info1:
    st.success("✅ **Indicadores Calculados Dinámicamente** - Basados en datos reales de la cooperativa")
    st.info(f"📊 **Mes de Referencia:** {mes_seleccionado}")
    st.info("🔄 **Actualización:** Los valores se recalculan automáticamente al cambiar el mes")

with col_info2:
    # Mostrar resumen de los cálculos basados en el mes seleccionado
    df_actual = dfs[mes_seleccionado]
    metricas_resumen = calcular_metricas_basicas(df_actual)

    st.metric("**Activos Totales**", ".2f")
    st.metric("**Ingresos Totales**", ".2f")
    st.metric("**Utilidad Neta**", ".2f")

    # Información adicional sobre fórmulas
    with st.expander("📖 Ver detalles de cálculo"):
        st.markdown(f"""
        **Fórmulas utilizadas:**

        - **ROA = (Utilidad Neta / Activos Totales) × 100**
          - Utilidad Neta = Ingresos - Gastos = {metricas_resumen['ingresos']:.2f} - {metricas_resumen['gastos']:.2f} = {metricas_resumen['utilidad_neta']:.2f}
          - ROA = ({metricas_resumen['utilidad_neta']:.2f} / {metricas_resumen['activos']:.2f}) × 100 = {indicadores_reales['roa']:.2f}%

        - **Eficiencia = (Ingresos - Gastos Operativos) / Ingresos × 100**
          - Calculado como: {indicadores_reales['eficiencia']:.2f}%

        - **Solvencia = (Patrimonio / Activos Totales) × 100**
          - Calculado como: {indicadores_reales['solvencia']:.2f}%
        """)

    # Mostrar estado de validación de datos
    st.markdown("---")
    st.subheader("🔍 Calidad de Datos")

    col_val1, col_val2, col_val3 = st.columns(3)

    with col_val1:
        st.metric("✅ Archivos Válidos", len(validacion_datos['archivos_validos']))

    with col_val2:
        if validacion_datos['archivos_con_advertencias']:
            st.metric("⚠️ Con Advertencias", len(validacion_datos['archivos_con_advertencias']))
        else:
            st.metric("⚠️ Con Advertencias", 0)

    with col_val3:
        if validacion_datos['archivos_con_errores']:
            st.metric("❌ Con Errores", len(validacion_datos['archivos_con_errores']))
        else:
            st.metric("❌ Con Errores", 0)

    # Mostrar detalles de validación si hay problemas
    if validacion_datos['archivos_con_errores'] or validacion_datos['archivos_con_advertencias']:
        with st.expander("📋 Ver detalles de validación"):
            if validacion_datos['archivos_con_errores']:
                st.error("**Archivos con errores:**")
                for archivo_error in validacion_datos['archivos_con_errores']:
                    st.write(f"**{archivo_error['archivo']}:**")
                    for error in archivo_error['errores']:
                        st.write(f"  - {error}")
                    if archivo_error['advertencias']:
                        for advertencia in archivo_error['advertencias']:
                            st.write(f"  - {advertencia}")

            if validacion_datos['archivos_con_advertencias']:
                st.warning("**Archivos con advertencias:**")
                for archivo_adv in validacion_datos['archivos_con_advertencias']:
                    st.write(f"**{archivo_adv['archivo']}:**")
                    for advertencia in archivo_adv['advertencias']:
                        st.write(f"  - {advertencia}")

    # Resumen de calidad de datos
    if len(validacion_datos['archivos_validos']) == validacion_datos['total_archivos']:
        st.success("🎉 **Todos los archivos de datos son válidos y están listos para análisis**")
    elif validacion_datos['archivos_con_errores']:
        st.error("⚠️ **Algunos archivos tienen errores que pueden afectar los cálculos**")
    else:
        st.info("ℹ️ **Los datos están en buen estado, pero revisa las advertencias**")


# Sidebar
with st.sidebar:
    st.image('padre_julian.png', width=240)
    st.markdown("## Menú Principal")
    st.markdown("---")
    # Utilizar 'expander' para organizar el contenido
    with st.expander("Ver Opciones"):
        seleccion_usuario = st.radio(
            "Selecciona una opción:",
            ('Inicio', 'Análisis', 'Proyecciones')
        )
    st.markdown("---")
    st.markdown("## Herramientas")
    # Ejemplo de un widget interactivo
    fecha_inicio = st.date_input("Selecciona fecha de inicio")
    fecha_fin = st.date_input("Selecciona fecha de fin")
    st.markdown("---")

    st.markdown("## Conéctate con Nosotros")
    st.button("Correo Electrónico")

    # Personalización visual con CSS
    st.markdown(
        """
        <style>
        .sidebar .sidebar-content {
            background-color: #f1f3f6;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

# Pestañas
tab1, tab2, tab3 = st.tabs(["ROA", "Eficiencia en gasto Operativo", "Solvencia Patrimonial"])

with tab1:
    st.header("Rentabilidad sobre el activo (ROA)")
    # Opciones para el cálculo del ROA
    opciones = ["Dos meses", "Trimestral", "Un año"]
    # Añade un select box para que el usuario elija el periodo de tiempo
    opcion_seleccionada = st.selectbox("Seleccione el periodo de tiempo para calcular el ROA:", opciones)
    meses = list(dfs.keys())  # Esto asumirá que ya tienes todos los meses cargados en 'dfs'
    trimestres = ["Enero - Marzo","Abril - Junio","Julio - Septiembre", "Octubre - Diciembre"]
    # Asegúrate de que solo se pueda seleccionar una opción


    if opcion_seleccionada == "Dos meses":
        mes = tres_meses = un_año = False
        col1, col2, col3 = st.columns([2,2,1])  # Dibuja los gráficos en sus respectivas columnas
        with col1:
            mes_inicio = st.selectbox(
                f"Seleccione el mes inicial para calcular el ROA    :",
                meses)
        with col2:
            mes_final = st.selectbox(f"Seleccione el mes final para calcular el ROA:",
                                     meses)
        with col3:
            año = st.selectbox(f"Seleccione el año para calcular el ROA:", ['2022','2023','2024'])
            if año == '2022':
                df_inicio = dfs2022[mes_inicio]
                df_final = dfs2022[mes_final]
            else:
                df_inicio = dfs[mes_inicio]
                df_final = dfs[mes_final]
        df_meses, ingresos, gastos, utilidad, roa = calcularROAMESES(mes_inicio,df_inicio,mes_final, df_final)
        fig_bar, fig_roa = crear_graficas_ROA(ingresos, gastos, utilidad, roa)
        # Crear un DataFrame con los datos
        df = pd.DataFrame({
            'Category': ['Ingresos Alcanzados', 'Ingresos Restantes'],
            'Amount': [11, 89]  # Asumiendo que el 50% es el ingreso alcanzado y el resto es el 50%.
        })

        # Crear un gráfico de anillo con Plotly Express
        fig = px.pie(df, values='Amount', names='Category', hole=0.7, title='Total ROA',
                     color_discrete_sequence=['#1f77b4', '#d62728', '#d62728'])

        # Personalizar el gráfico para que se parezca al de la imagen
        fig.update_traces(textinfo='none')  # Ocultar el texto dentro de las porciones
        fig.update_layout(
            showlegend=False,  # Ocultar la leyenda
            annotations=[dict(text='2.13%', x=0.5, y=0.5, font_size=20, showarrow=False)],  # Porcentaje en el centro
            margin=dict(t=0, b=0, l=15, r=0),  # Eliminar márgenes
        )

        # Agregar texto extra con update_layout (tendrás que ajustar la posición según sea necesario)
        fig.add_annotation(x=0.5, y=0.3, text="$0.02318775", showarrow=False, font_size=15)
        fig.add_annotation(x=0.5, y=0.2, text="Total ROA", showarrow=False, font_size=12)

        # Ajustar la orientación del gráfico
        fig.update_layout(autosize=False, width=300, height=300)
        col3,col4 = st.columns([2.5,1.5])
        with col3:
            st.plotly_chart(fig_bar)

        with col4:
            st.write(df_meses)
            st.plotly_chart(fig)
        categoria_para_graficar = st.selectbox("Selecciona la categoría para graficar",
                                               ['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta',
                                                'Activo Promedio', 'ROA'])

        grafico2 = graficoMes(df_meses, categoria_para_graficar)
        st.plotly_chart(grafico2, use_container_width=True)



    elif opcion_seleccionada == "Trimestral":

        def procesar_datos_trimestrales(trimestre, dfs):
            # Configura los meses de acuerdo al trimestre seleccionado
            if trimestre == "Enero - Marzo":
                meses = ["Enero", "Febrero", "Marzo"]
            elif trimestre == "Abril - Junio":
                meses = ["Abril", "Mayo", "Junio"]
            elif trimestre == "Julio - Septiembre":
                meses = ["Julio", "Agosto", "Septiembre"]
            elif trimestre == "Octubre - Diciembre":
                meses = ["Octubre", "Noviembre", "Noviembre"]

            # Realiza el cálculo para el trimestre usando los DataFrames correctos
            df_trimestre,df_ROA_trimestres, ingresos, gastos, utilidad, roa_trimestres = calcularROATRIMESTRE(meses[0], dfs[meses[0]],
                                                                                 meses[1], dfs[meses[1]],
                                                                                 meses[2], dfs[meses[2]])
            # Crea los gráficos
            fig_bar, fig_roa = crear_graficas_ROA(ingresos, gastos, utilidad, roa_trimestres)
            # Inicializa una lista para almacenar los resultados del ROA


            # Ahora puedes utilizar 'df_resultados_roa' para crear el gráfico de anillo
            fig_anillo = crear_grafico_anillo(df_ROA_trimestres, 'ROA por Mes', 'ROA', 'Mes')

            return df_trimestre, fig_bar, fig_roa,fig_anillo,df_ROA_trimestres,roa_trimestres


        mes = dos_meses = un_año = False
        col1, col2= st.columns(2)
        with col1:
            trimestre = st.selectbox(f"Selecciona el trimestre para calcular el ROA de {opcion_seleccionada.lower()}:",
                                 trimestres)
        with col2:
            año = st.selectbox(f"Seleccione el año para calcular el ROA de {opcion_seleccionada.lower()}:", ['2022','2023','2024'])
            if año == '2022':
                df_trimestre, fig_bar, fig_roa,ovalo,df_ROA_trimestres,roa_trimestres = procesar_datos_trimestrales(trimestre, dfs2022)
            else:
                df_trimestre, fig_bar, fig_roa,ovalo,df_ROA_trimestres,roa_trimestres = procesar_datos_trimestrales(trimestre, dfs)

        col3, col4 = st.columns([2.5, 1.5])
        with col3:
            st.metric("Solvencia Patrimonial de dos meses", f"{roa_trimestres:.2f}%")
            st.plotly_chart(fig_bar)
        with col4:
            st.write(df_trimestre)
            st.plotly_chart(ovalo)

        categoria_para_graficar = st.selectbox("Selecciona la categoría para graficar",
                                               ['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta',
                                                'Activo Promedio', 'ROA'])
        grafico2 = graficoMes(df_trimestre, categoria_para_graficar)
        st.plotly_chart(grafico2, use_container_width=True)

    elif opcion_seleccionada == "Un año":
        mes = dos_meses = tres_meses = False

        col5,col6 = st.columns(2)

        with col6:
            año_año = st.selectbox("Selecciona el año para graficar",["2022",'2023','2024'])
            if año_año == "2022":
                resultados_df, ingresos_totales, gastos_totales, utilidad_neta, activo_promedio, ROA = calcularROAAnual(
                    dfs2022)
            else:
                resultados_df, ingresos_totales, gastos_totales, utilidad_neta, activo_promedio, ROA = calcularROAAnual(
                    dfs)
        with col5:
            st.metric("Solvencia Patrimonial de un año", f"{ROA:.2f}%")

        datos_anuales = {
            'Categoria': ['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta', 'Activo Promedio'],
            'Valor': [ingresos_totales, gastos_totales, utilidad_neta, activo_promedio]
        }
        datos_anuales_df = pd.DataFrame(datos_anuales)

        # Graficar según la selección del usuario
        grafico1,pai = crear_grafico(datos_anuales_df, "ROA Anual",resultados_df)
        # Divide la página en dos columnas para los gráficos
        col1, col2 = st.columns([3,1])        # Dibuja los gráficos en sus respectivas columnas
        with col1:
            st.plotly_chart(grafico1, use_container_width=True)

        with col2:
            st.plotly_chart(pai, use_container_width=True)
        categoria_para_graficar = st.selectbox("Selecciona la categoría para graficar",
                                               ['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta',
                                                'Activo Promedio', 'ROA'])

        grafico2 = graficoMes(resultados_df, categoria_para_graficar)

        # Convertir el DataFrame en un objeto Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            resultados_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)

        # Crear el botón de descarga en Streamlit, que ofrecerá el archivo Excel generado
        btn = download_button(
            label="Descargar datos en Excel",
            data=output,
            file_name="datos_anuales.xlsx",
            mime="application/vnd.ms-excel"
        )

        col5, col6 = st.columns([1.5, 2.5])
        with col5:
            st.write(resultados_df)
        with col6:
            if btn:
                st.success('¡Descarga exitosa!')
            st.plotly_chart(grafico2, use_container_width=True)

with tab2:
    def calcularEficienciaGastoOperativo(df):
        # Calcular los Ingresos Totales
        ingresos_totales = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        # Calcular los Gastos Operativos
        gastos_operativos = df[df["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
        # Calcular la Eficiencia en Gasto Operativo
        eficiencia_gasto_operativo = (ingresos_totales - gastos_operativos) / ingresos_totales
        # Retornar la Eficiencia en Gasto Operativo

        st.subheader("Eficiencia en gasto operativo")
        st.write("Ingresos_totales", ingresos_totales)
        st.write("Gastos_operativos ", gastos_operativos)
        st.write("Eficiencia en gasto operativo ", eficiencia_gasto_operativo)

        return eficiencia_gasto_operativo

    def eficiencia_2_meses(df, df2, mes_inicio, mes_final):
        # Calcular los datos para el primer mes
        ingresos_totales1 = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        gastos_operativos1 = df[df["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
        eficiencia_gasto_operativo1 = (ingresos_totales1 - gastos_operativos1) / ingresos_totales1

        # Calcular los datos para el segundo mes
        ingresos_totales2 = df2[df2["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        gastos_operativos2 = df2[df2["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
        eficiencia_gasto_operativo2 = (ingresos_totales2 - gastos_operativos2) / ingresos_totales2

        # Crear un DataFrame con los resultados
        resultados = pd.DataFrame({
            'Mes': [mes_inicio, mes_final],
            'Ingresos Totales': [ingresos_totales1, ingresos_totales2],
            'Gastos Operativos': [gastos_operativos1, gastos_operativos2],
            'Eficiencia por Gasto Operativo': [eficiencia_gasto_operativo1, eficiencia_gasto_operativo2]
        })

        return resultados

    def eficiencia_trimestral(df1, df2, df3, mes1, mes2, mes3):
        # Calcular los datos para el primer mes
        ingresos_totales1 = df1[df1["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        gastos_operativos1 = df1[df1["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
        eficiencia_gasto_operativo1 = (
                                                  ingresos_totales1 - gastos_operativos1) / ingresos_totales1 if ingresos_totales1 else 0

        # Calcular los datos para el segundo mes
        ingresos_totales2 = df2[df2["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        gastos_operativos2 = df2[df2["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
        eficiencia_gasto_operativo2 = (
                                                  ingresos_totales2 - gastos_operativos2) / ingresos_totales2 if ingresos_totales2 else 0

        # Calcular los datos para el tercer mes
        ingresos_totales3 = df3[df3["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
        gastos_operativos3 = df3[df3["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
        eficiencia_gasto_operativo3 = (
                                                  ingresos_totales3 - gastos_operativos3) / ingresos_totales3 if ingresos_totales3 else 0

        # Crear un DataFrame con los resultados
        resultados_trimestrales = pd.DataFrame({
            'Mes': [mes1, mes2, mes3],
            'Ingresos Totales': [ingresos_totales1, ingresos_totales2, ingresos_totales3],
            'Gastos Operativos': [gastos_operativos1, gastos_operativos2, gastos_operativos3],
            'Eficiencia por Gasto Operativo': [eficiencia_gasto_operativo1, eficiencia_gasto_operativo2,
                                               eficiencia_gasto_operativo3]
        })

        return resultados_trimestrales


    def eficienciaAnual(dfs):
        # Crear listas para almacenar datos de cada mes
        meses = []
        ingresos_mensuales = []
        gastos_operativos_mensuales = []

        # Recorrer todos los DataFrames
        for mes, df in dfs.items():
            meses.append(mes)
            ingresos_totales = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
            gastos_operativos = df[df["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()

            ingresos_mensuales.append(ingresos_totales)
            gastos_operativos_mensuales.append(gastos_operativos)

        # Crear un DataFrame con los datos recopilados
        df_resultados_anuales = pd.DataFrame({
            'Mes': meses,
            'Ingresos Totales': ingresos_mensuales,
            'Gastos Operativos': gastos_operativos_mensuales
        })



        return df_resultados_anuales


    import plotly.express as px


    def graficar_ingresos_gastos_anuales(df_resultados_anuales):
        fig = px.line(df_resultados_anuales, x='Mes', y=['Ingresos Totales', 'Gastos Operativos'],
                      markers=True, title='Ingresos y Gastos Operativos Anuales')
        fig.update_layout(yaxis_title='Cantidad', xaxis_title='Mes')
        return fig


    def visualizar_eficiencia_anual_plotly(dfs):
        # Crear listas para almacenar los datos de mes y eficiencia
        meses = []
        eficiencias = []

        # Iterar sobre cada DataFrame mensual en el diccionario 'dfs'
        for mes, df in dfs.items():
            ingresos_totales = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
            gastos_operativos = df[df["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
            eficiencia = (ingresos_totales - gastos_operativos) / ingresos_totales if ingresos_totales > 0 else 0

            # Añadir los datos a las listas
            meses.append(mes)
            eficiencias.append(eficiencia)

        # Crear un gráfico de línea con Plotly
        fig = go.Figure(data=go.Scatter(x=meses, y=eficiencias, mode='lines+markers', name='Eficiencia'))
        fig.update_layout(title='Eficiencia en Gasto Operativo Anual',
                          xaxis_title='Mes',
                          yaxis_title='Eficiencia',
                          yaxis=dict(tickformat=".2%"))  # Formato de porcentaje

        return fig


    def visualizar_eficiencia_trimestral_plotly_express(df1, df2, df3, nombres_meses):
        data = []

        for df_actual, nombre_mes in zip([df1, df2, df3], nombres_meses):
            ingresos_totales = df_actual[df_actual["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
            gastos_operativos = df_actual[df_actual["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
            eficiencia = (ingresos_totales - gastos_operativos) / ingresos_totales if ingresos_totales > 0 else 0
            data.append({'Mes': nombre_mes, 'Eficiencia': eficiencia})

        df_eficiencia = pd.DataFrame(data)
        fig = px.line(df_eficiencia, x='Mes', y='Eficiencia', markers=True,
                      title='Eficiencia en Gasto Operativo - Trimestral')
        fig.update_layout(xaxis_title='Mes del Trimestre', yaxis_title='Eficiencia', yaxis=dict(tickformat=".2%"))

        return fig, df_eficiencia

    def grafico_barras_dobles_ingresos_gastos(df1, df2, df3, nombres_meses):
        # Inicializar listas para almacenar los datos
        ingresos = []
        gastos_operativos = []

        # Iterar sobre cada DataFrame y extraer los datos requeridos
        for df_actual in [df1, df2, df3]:
            ingresos_totales = df_actual[df_actual["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
            gastos_operativos_totales = df_actual[df_actual["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
            ingresos.append(ingresos_totales)
            gastos_operativos.append(gastos_operativos_totales)

        # Crear el gráfico de barras dobles
        fig = go.Figure(data=[
            go.Bar(name='Ingresos', x=nombres_meses, y=ingresos),
            go.Bar(name='Gastos Operativos', x=nombres_meses, y=gastos_operativos)
        ])

        # Cambiar el diseño del gráfico para poner las barras una al lado de la otra
        fig.update_layout(barmode='group', title="Ingresos vs Gastos Operativos por Mes")

        return fig


    def graficar_ingresos_gastos(df):
        # Crear un gráfico de barras dobles para Ingresos y Gastos Operativos
        fig = px.bar(df, x='Mes', y=['Ingresos Totales', 'Gastos Operativos'],
                     barmode='group', title='Ingresos vs Gastos Operativos por Mes')

        # Configuraciones adicionales para mejorar la visualización
        fig.update_layout(
            yaxis_title='Cantidad',
            xaxis_tickangle=-45,
            legend_title='Categoría'
        )
        fig.update_traces(texttemplate='%{y}', textposition='outside')

        return fig


    def calcular_datos_anuales(dfs):
        # Inicializar listas para almacenar los datos
        meses = []
        ingresos_por_mes = []
        gastos_por_mes = []
        eficiencia_por_mes = []

        # Recorrer el diccionario de DataFrames y calcular los datos requeridos
        for mes, df in dfs.items():
            meses.append(mes)
            ingresos = df[df["TIPO"] == 5]["PADRE JULIAN LORENTE LTDA"].sum()
            gastos = df[df["CODIGO_CONTABLE"] == 45]["PADRE JULIAN LORENTE LTDA"].sum()
            eficiencia = (ingresos - gastos) / ingresos if ingresos > 0 else 0

            ingresos_por_mes.append(ingresos)
            gastos_por_mes.append(gastos)
            eficiencia_por_mes.append(eficiencia)

        # Calcular totales y eficiencia global
        ingresos_totales = sum(ingresos_por_mes)
        gastos_totales = sum(gastos_por_mes)
        eficiencia_global = (ingresos_totales - gastos_totales) / ingresos_totales if ingresos_totales > 0 else 0

        # Crear el DataFrame
        df_resultados = pd.DataFrame({
            'Mes': meses + ['Total'],
            'Ingresos': ingresos_por_mes + [ingresos_totales],
            'Gastos': gastos_por_mes + [gastos_totales],
            'Eficiencia': eficiencia_por_mes + [eficiencia_global]
        })

        return df_resultados


    with tab2:

        st.header("Eficiencia en gasto operativo")

        # Añade un select box para que el usuario elija el periodo de tiempo
        opcion_seleccionada = st.selectbox("Seleccione el periodo de tiempo para calcular la eficiencia:", opciones)
        meses = list(dfs.keys())  # Esto asumirá que ya tienes todos los meses cargados en 'dfs'
        trimestres = ["Enero - Marzo", "Abril - Junio", "Julio - Septiembre", "Octubre - Diciembre"]

        # Asegúrate de que solo se pueda seleccionar una opción
        if opcion_seleccionada == "Un mes":
            dos_meses = tres_meses = un_año = False
            mes_inicio = st.selectbox(
                f"Seleccione el mes inicial para calcular la eficiencia de {opcion_seleccionada.lower()}:",
                meses)
            df_seleccionado = dfs[mes_inicio]
            calcularEficienciaGastoOperativo(df_seleccionado)




        elif opcion_seleccionada == "Dos meses":
            mes = tres_meses = un_año = False
            col1, col2,col3 = st.columns(3)
            with col1:
                mes_inicio = st.selectbox(
                "Seleccione el mes inicial para calcular la eficiencia de dos meses:",
                meses)
            with col2:
                mes_final = st.selectbox(
                "Seleccione el mes final para calcular la eficiencia de dos meses:",
                meses)
            with col3:
                año = st.selectbox(f"Seleccione el año para calcular la eficiencia:", ['2022', '2023', '2024'])
                if año == '2022':
                    df_inicio = dfs2022[mes_inicio]
                    df_final = dfs2022[mes_final]
                else:
                    df_inicio = dfs[mes_inicio]
                    df_final = dfs[mes_final]

            # Llamada a la función modificada
            resultados_eficiencia = eficiencia_2_meses(df_inicio, df_final, mes_inicio, mes_final)
            # Crear un gráfico de anillo con Plotly Express
            fig = px.pie(resultados_eficiencia, values='Eficiencia por Gasto Operativo', names='Mes', hole=0.7, title='Total ROA')

            # Personalizar el gráfico para que se parezca al de la imagen
            fig.update_traces(textinfo='none')  # Ocultar el texto dentro de las porciones
            fig.update_layout(
                showlegend=False,  # Ocultar la leyenda
                annotations=[dict(text='2.13%', x=0.5, y=0.5, font_size=20, showarrow=False)],
                # Porcentaje en el centro
                margin=dict(t=0, b=0, l=15, r=0),  # Eliminar márgenes
            )

            # Agregar texto extra con update_layout (tendrás que ajustar la posición según sea necesario)
            fig.add_annotation(x=0.5, y=0.3, text="$0.02318775", showarrow=False, font_size=15)
            fig.add_annotation(x=0.5, y=0.2, text="Total ROA", showarrow=False, font_size=12)

            # Ajustar la orientación del gráfico
            fig.update_layout(autosize=False, width=300, height=300)
            col3, col4 = st.columns([2, 2])
            with col3:
                st.markdown("&#180;")
            # Visualización del DataFrame con Streamlit
                st.dataframe(resultados_eficiencia)
                st.plotly_chart(fig)


            # Asegúrate de tener los resultados en el DataFrame resultados_eficiencia
            # como se describió en los pasos anteriores

            # Llamada a la función para crear el gráfico
            figura_ingresos_gastos = graficar_ingresos_gastos(resultados_eficiencia)
            with col4:
            # Mostrar el gráfico en Streamlit
                st.plotly_chart(figura_ingresos_gastos)







        # Ejemplo para un Gráfico de Línea de Tendencia

        elif opcion_seleccionada == "Trimestral":

            mes = dos_meses = un_año = False


            trimestre = st.selectbox(

                "Selecciona el trimestre para calcular la eficiencia:",

                trimestres

            )
            col1, col2 = st.columns([1.5, 2.5])
            if trimestre == "Enero - Marzo":

                # Llamada a la función ajustada para el trimestre seleccionado

                resultados_eficiencia = eficiencia_trimestral(

                    dfs["Enero"], dfs["Febrero"], dfs["Marzo"],

                    "Enero", "Febrero", "Marzo"

                )

                nombres_meses = ["Enero", "Febrero", "Marzo"]
                grafico_eficiencia, df_eficiencia = visualizar_eficiencia_trimestral_plotly_express(
                    dfs["Enero"], dfs["Febrero"], dfs["Marzo"], nombres_meses


                )
                grafico = grafico_barras_dobles_ingresos_gastos(dfs["Enero"], dfs["Febrero"], dfs["Marzo"],
                                                                nombres_meses)


            elif trimestre == "Abril - Junio":

                resultados_eficiencia = eficiencia_trimestral(

                    dfs["Abril"], dfs["Mayo"], dfs["Junio"],

                    "Abril", "Mayo", "Junio"

                )

                nombres_meses = ["Abril", "Mayo", "Junio"]
                grafico_eficiencia, df_eficiencia = visualizar_eficiencia_trimestral_plotly_express(
                    dfs["Abril"], dfs["Mayo"], dfs["Junio"], nombres_meses

                )
                grafico = grafico_barras_dobles_ingresos_gastos(dfs["Abril"], dfs["Mayo"], dfs["Junio"],
                                                                nombres_meses)


            elif trimestre == "Julio - Septiembre":

                resultados_eficiencia = eficiencia_trimestral(

                    dfs["Julio"], dfs["Agosto"], dfs["Septiembre"],

                    "Julio", "Agosto", "Septiembre"

                )

                nombres_meses = ["Julio", "Agosto", "Septiembre"]
                grafico_eficiencia, df_eficiencia = visualizar_eficiencia_trimestral_plotly_express(
                    dfs["Julio"], dfs["Agosto"], dfs["Septiembre"], nombres_meses

                )
                grafico = grafico_barras_dobles_ingresos_gastos(dfs["Julio"], dfs["Agosto"], dfs["Septiembre"],
                                                                nombres_meses)


            elif trimestre == "Octubre - Diciembre":

                # Aquí asumo que tienes un DataFrame para diciembre también.

                # Si no es el caso, ajusta según tus DataFrames disponibles.

                resultados_eficiencia = eficiencia_trimestral(

                    dfs["Octubre"], dfs["Noviembre"], dfs["Noviembre"],

                    "Octubre", "Noviembre", "Noviembre"

                )

                nombres_meses = ["Octubre", "Noviembre", "Diciembre"]
                grafico_eficiencia, df_eficiencia = visualizar_eficiencia_trimestral_plotly_express(
                    dfs["Octubre"], dfs["Noviembre"], dfs["Noviembre"], nombres_meses

                )
                grafico = grafico_barras_dobles_ingresos_gastos(dfs["Octubre"], dfs["Noviembre"], dfs["Noviembre"],
                                                                nombres_meses)


            # Visualización del DataFrame con Streamlit
            with col1:
                st.markdown("&#180;")
                st.dataframe(resultados_eficiencia)
            with col2:
                st.plotly_chart(grafico_eficiencia, use_container_width=True)

            st.plotly_chart(grafico, use_container_width=True)




        elif opcion_seleccionada == "Un año":
            mes = dos_meses = tres_meses = False
            col1, col2 = st.columns([1.5, 1.5])
            eficienciaAnual(dfs)  # Aquí necesitarías el DataFrame con los datos de todo el año
            # Asumiendo que 'dfs' ya está definido y contiene los DataFrames mensuales
            # Calcular los datos anuales
            df_resultados_anuales = calcular_datos_anuales(dfs)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df_resultados_anuales.to_excel(writer, index=False, sheet_name='Sheet1')
            output.seek(0)

            # Crear el botón de descarga en Streamlit, que ofrecerá el archivo Excel generado
            btn_solvencia = download_button(
                label="Descargar datos en Excel",
                data=output,
                file_name="datos_eficiencia_operativa.xlsx",
                mime="application/vnd.ms-excel",
                key="unique_key_eficiencia"  # Reemplaza 'unique_key_solvencia' con una clave única
            )

            # Mostrar la tabla en Streamlit
            with col1:
                st.dataframe(df_resultados_anuales, height=400, width=700)

            with col2:            # Crear la gráfica de líneas

                grafico_eficiencia = visualizar_eficiencia_anual_plotly(dfs)
                st.plotly_chart(grafico_eficiencia, use_container_width=True)
            if btn_solvencia:
                st.success('¡Descarga exitosa!')
            # Obtener los datos anuales
            df_resultados_anuales = eficienciaAnual(dfs)


            # Crear la gráfica de líneas
            fig_ingresos_gastos_anuales = graficar_ingresos_gastos_anuales(df_resultados_anuales)

            # Mostrar la gráfica en Streamlit
            st.plotly_chart(fig_ingresos_gastos_anuales, use_container_width=True)



with tab3:
    st.header("Solvencia Patrimonial")
    # Opciones para el cálculo del ROA
    opciones = ["Dos meses", "Trimestral", "Un año"]
    # Añade un select box para que el usuario elija el periodo de tiempo
    opcion_seleccionada = st.selectbox("Seleccione el periodo de tiempo para calcular la solvencia Patrimonial:", opciones)
    meses = list(dfs.keys())  # Esto asumirá que ya tienes todos los meses cargados en 'dfs'
    trimestres = ["Enero - Marzo", "Abril - Junio", "Julio - Septiembre", "Octubre - Diciembre"]
    # Asegúrate de que solo se pueda seleccionar una opción

    if opcion_seleccionada == "Dos meses":
        mes = tres_meses = un_año = False
        col1, col2, col3 = st.columns([2, 2, 1])  # Dibuja los gráficos en sus respectivas columnas
        with col1:
            mes_inicio = st.selectbox(
                f"Seleccione el mes inicial para calcular la solvencia Patrimonial:",
                meses)
        with col2:
            mes_final = st.selectbox(f"Seleccione el mes final para calcular la solvencia Patrimonial:",
                                     meses)
        with col3:
            año = st.selectbox(f"Seleccione el año:", ['2022', '2023', '2024'])
            if año == '2022':
                df_inicio = dfs2022[mes_inicio]
                df_final = dfs2022[mes_final]
            else:
                df_inicio = dfs[mes_inicio]
                df_final = dfs[mes_final]
        df_solvencia,solvencia_patrimonial, patrimonio_promedio, activo_total_promedio = calcularSolvenciaPatrimonialDosMeses(df_inicio, df_final,mes_inicio,mes_final)
        # Llamada a la función para crear el gráfico de barras y el gráfico de pastel de solvencia patrimonial
        fig_bar_solvencia, fig_pie_meses = crear_grafico_solvencia_meses(df_solvencia, "Solvencia Patrimonial Mensual",
                                                   "Solvencia Patrimonial (%)",
                                                    patrimonio_promedio, activo_total_promedio,solvencia_patrimonial)

        # Crear un DataFrame con los datos
        df = pd.DataFrame({
            'Category': ['Ingresos Alcanzados', 'Ingresos Restantes'],
            'Amount': [11, 89]  # Asumiendo que el 50% es el ingreso alcanzado y el resto es el 50%.
        })

        # Crear un gráfico de anillo con Plotly Express
        fig = px.pie(df, values='Amount', names='Category', hole=0.7, title='Total ROA')

        # Personalizar el gráfico para que se parezca al de la imagen
        fig.update_traces(textinfo='none')  # Ocultar el texto dentro de las porciones
        fig.update_layout(
            showlegend=False,  # Ocultar la leyenda
            annotations=[dict(text='2.13%', x=0.5, y=0.5, font_size=20, showarrow=False)],  # Porcentaje en el centro
            margin=dict(t=0, b=0, l=15, r=0),  # Eliminar márgenes
        )

        # Agregar texto extra con update_layout (tendrás que ajustar la posición según sea necesario)
        fig.add_annotation(x=0.5, y=0.3, text="$0.02318775", showarrow=False, font_size=15)
        fig.add_annotation(x=0.5, y=0.2, text="Total ROA", showarrow=False, font_size=12)

        # Ajustar la orientación del gráfico
        fig.update_layout(autosize=False, width=300, height=300)
        col3, col4 = st.columns([2.5, 1.5])
        with col3:
            st.metric("Solvencia Patrimonial de dos meses", f"{solvencia_patrimonial:.2f}%")
            st.plotly_chart(fig_bar_solvencia)

        with col4:
            st.write(df_solvencia)
            st.plotly_chart(fig_pie_meses)
        categoria_para_graficar = st.selectbox("Selecciona la categoría para realizar la grafica",
                                               ['Patrimonio', 'Activo Total', 'Solvencia Patrimonial (%)'])

        grafico2 = graficoMes(df_solvencia, categoria_para_graficar)
        st.plotly_chart(grafico2, use_container_width=True)



    elif opcion_seleccionada == "Trimestral":
        mes = dos_meses = un_año = False
        col1, col2 = st.columns(2)

        with col1:
            trimestre = st.selectbox("Selecciona el trimestre para calcular la Solvencia Patrimonial:", trimestres)

        with col2:
            año = st.selectbox("Seleccione el año para calcular la Solvencia Patrimonial:", ['2022', '2023', '2024'])

        # Determinar los DataFrames de cada mes basado en el año seleccionado

        if año == '2022':
            dfs_actual = dfs2022
        else:
            dfs_actual = dfs

        # Obtener los nombres de los meses basados en el trimestre seleccionado

        if trimestre == "Enero - Marzo":
            meses = ["Enero", "Febrero", "Marzo"]
        elif trimestre == "Abril - Junio":
            meses = ["Abril", "Mayo", "Junio"]
        elif trimestre == "Julio - Septiembre":
            meses = ["Julio", "Agosto", "Septiembre"]
        elif trimestre == "Octubre - Diciembre":
            meses = ["Octubre", "Noviembre", "Noviembre"]

        # Calcular la solvencia patrimonial para cada mes del trimestre

        solvencia_mensual = []

        for mes in meses:
            df_mes = dfs_actual[mes]

            solvencia = calcularSolvenciaPatrimonialUnMes(df_mes, mes)

            solvencia_mensual.append(solvencia)

        # Crear un DataFrame con los resultados

        df_solvencia_trimestre = pd.concat(solvencia_mensual).reset_index(drop=True)

        solvencia_patrimonial_promedio = df_solvencia_trimestre['Solvencia Patrimonial (%)'].mean()

        # Crear los gráficos


        fig_bar_solvencia = go.Figure(data=[
            go.Scatter(x=df_solvencia_trimestre['Mes'], y=df_solvencia_trimestre['Activo Total'], name='Activo Total')
        ])
        # Actualizar el diseño del gráfico
        fig_bar_solvencia.update_layout(
            title='Solvencia Patrimonial por Mes',
            xaxis_title='Mes',
            yaxis_title='Activo Total',
            yaxis=dict(tickformat=',')  # Formato con comas para los números
        )
        fig_pie_solvencia = px.pie(df_solvencia_trimestre, names='Mes', values='Solvencia Patrimonial (%)',
                                   title='Distribución de la Solvencia Patrimonial')

        # Presentar los gráficos y datos en Streamlit

        col3, col4 = st.columns([2, 1])

        with col3:
            st.metric("Solvencia Patrimonial Promedio del Trimestre", f"{solvencia_patrimonial_promedio:.2f}%")

            st.plotly_chart(fig_bar_solvencia, use_container_width=True)

        with col4:
            st.write(df_solvencia_trimestre)

            st.plotly_chart(fig_pie_solvencia, use_container_width=True)

        # Mostrar la tabla de resultados y el promedio






    elif opcion_seleccionada == "Un año":
        mes = dos_meses = tres_meses = False
        col3, col4 = st.columns(2)
        with col3:
            categoria_para_graficar = st.selectbox("Selecciona la categoría para realizar la grafica",
                                                   ['Ingresos Totales', 'Gastos Totales', 'Utilidad Neta',
                                                    'Activo Promedio', 'ROA'])
        with col4:
            año = st.selectbox("Selecciona un año ", ['2022', '2023', '2024'])
            if año == '2022':
                resultados_anuales_df, resultados_solvencia_df, solvencia_patrimonial_anual, patrimonio_promedio, activo_total_promedio = calcularSolvenciaPatrimonialAnual(
                    dfs2022)
            else:
                resultados_anuales_df, resultados_solvencia_df, solvencia_patrimonial_anual, patrimonio_promedio, activo_total_promedio = calcularSolvenciaPatrimonialAnual(
                    dfs)

        # Crear los gráficos para la solvencia patrimonial anual
        grafico_solvencia_anual, grafico_pie_anual = crear_grafico_solvencia(resultados_solvencia_df,
                                                                             "Solvencia Patrimonial Anual",
                                                                             "Solvencia Patrimonial (%)",
                                                                             patrimonio_promedio, activo_total_promedio,
                                                                             solvencia_patrimonial_anual)

        # Mostrar resultados y gráficos en Streamlit
        col1, col2 = st.columns([3, 1])
        with col1:
            st.metric("Solvencia Patrimonial Anual", f"{solvencia_patrimonial_anual:.2f}%")
            st.plotly_chart(grafico_solvencia_anual, use_container_width=True)
        with col2:
            st.plotly_chart(grafico_pie_anual, use_container_width=True)
        categoria_para_graficar = st.selectbox("Selecciona la categoría para realizar la grafica",
                                               ['Patrimonio Promedio', 'Activo Total Promedio', 'Solvencia Patrimonial'])

        grafico2 = graficoMes(resultados_solvencia_df, categoria_para_graficar)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            resultados_solvencia_df.to_excel(writer, index=False, sheet_name='Sheet1')
        output.seek(0)

        # Crear el botón de descarga en Streamlit, que ofrecerá el archivo Excel generado
        btn_solvencia = download_button(
            label="Descargar datos en Excel",
            data=output,
            file_name="datos_solvencia.xlsx",
            mime="application/vnd.ms-excel",
            key="unique_key_solvencia"  # Reemplaza 'unique_key_solvencia' con una clave única
        )
        col5, col6 = st.columns([1.5, 2.5])
        with col5:
            st.write(resultados_solvencia_df)
        with col6:
            if btn_solvencia:
                st.success('¡Descarga exitosa!')
            st.plotly_chart(grafico2, use_container_width=True)