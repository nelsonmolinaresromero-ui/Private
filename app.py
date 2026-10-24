import pandas as pd
import streamlit as st

# =====================================================================
# PARÁMETROS: aquí cambias todo sin tocar el resto del código
# =====================================================================
ARCHIVO = "Notas_Consolidadas_2026-2.csv"

TITULO_PAGINA = "Notas 2026-2"
ICONO = "📊"
TITULO = "Tablero de notas 2026-2"
DESCRIPCION = "Consolidado de cortes 1 y 2. Usa los filtros de la barra lateral (en el celular, el botón » de arriba a la izquierda) para explorar los datos."

# Nombres de las columnas del CSV
COL_CURSO = "Curso"
COL_GRUPO = "Grupo"
COL_CORTE = "Corte"
COL_NOTA = "Nota"
COL_PESO = "Peso"
COL_ESTUDIANTE = "Estudiante"
COLS_TEXTO = ["Código", "Grupo"]  # se leen como texto para conservar ceros ("0407")

# Reglas
NOTA_MINIMA_DEFAULT = 3.0   # desde esta nota se considera ganada
NOTA_MAX = 5.0
DECIMALES = 2

# Textos de la barra lateral
ETQ_RANGO = "Rango de cortes"
ETQ_CURSOS = "Cursos"
ETQ_GRUPOS = "Grupos"
ETQ_UMBRAL = "Nota mínima para ganar"

# Secciones
SEC_KPI = "Indicadores generales"
SEC_CURSO = "Resultados por curso"
SEC_GRAFICOS = "Análisis visual"
SEC_TABLA = "Detalle de notas"

# Tarjetas de indicadores (usan las NOTAS DEFINITIVAS): (nombre en la tarjeta, qué calcular)
# Opciones de cálculo: "ganaron", "perdieron", "promedio", "pct_ganaron",
#                      "estudiantes", "total", "maxima", "minima"
TARJETAS = [
    ("Definitivas ganadas", "ganaron"),
    ("Definitivas perdidas", "perdieron"),
    ("Promedio de definitivas", "promedio"),
    ("% de definitivas ganadas", "pct_ganaron"),
]

# Gráficos: (título, tipo, parámetros)
#   tipo "barras": cuenta las notas ganadas por la columna "por", separadas por corte
#   tipo "lineas": promedio de la nota por "x", con una línea por cada "serie"
GRAFICOS = [
    {"titulo": "Notas ganadas por curso", "tipo": "barras", "por": COL_CURSO},
    {"titulo": "Evolución del promedio por corte", "tipo": "lineas",
     "x": COL_CORTE, "serie": COL_CURSO},
]

# =====================================================================
# CÓDIGO (no necesitas cambiar nada de aquí hacia abajo)
# =====================================================================
st.set_page_config(
    page_title=TITULO_PAGINA,
    page_icon=ICONO,
    layout="wide",
    initial_sidebar_state="auto",  # en el celular el menú de filtros arranca cerrado
)

# Ajustes para pantallas pequeñas (celular): menos márgenes, texto más compacto
# y tarjetas de indicadores de 2 en 2 en lugar de una debajo de otra.
st.markdown(
    """
    <style>
    @media (max-width: 640px) {
        .block-container { padding: 1rem 0.75rem 3rem 0.75rem; }
        h1 { font-size: 1.6rem !important; }
        h2 { font-size: 1.3rem !important; }
        h3 { font-size: 1.1rem !important; }
        [data-testid="stMetricValue"] { font-size: 1.5rem; }
        [data-testid="stMetricLabel"] p { font-size: 0.8rem; }
        .st-key-tarjetas [data-testid="stColumn"] {
            min-width: calc(50% - 0.5rem) !important;
            flex: 1 1 calc(50% - 0.5rem) !important;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def cargar():
    return pd.read_csv(ARCHIVO, encoding="utf-8-sig", dtype={c: str for c in COLS_TEXTO})


df = cargar()

st.title(f"{ICONO} {TITULO}")
st.caption(DESCRIPCION)

# ---------------- Barra lateral: filtros ----------------
st.sidebar.header("Filtros")

corte_min, corte_max = int(df[COL_CORTE].min()), int(df[COL_CORTE].max())
rango = st.sidebar.slider(ETQ_RANGO, corte_min, corte_max, (corte_min, corte_max))

cursos = sorted(df[COL_CURSO].unique())
cursos_sel = st.sidebar.multiselect(ETQ_CURSOS, cursos, default=cursos)

grupos = sorted(df[df[COL_CURSO].isin(cursos_sel)][COL_GRUPO].unique())
grupos_sel = st.sidebar.multiselect(ETQ_GRUPOS, grupos, default=grupos)

umbral = st.sidebar.number_input(
    ETQ_UMBRAL, min_value=0.0, max_value=NOTA_MAX, value=NOTA_MINIMA_DEFAULT, step=0.1
)

# ---------------- Aplicar filtros ----------------
filtrado = df[
    df[COL_CORTE].between(rango[0], rango[1])
    & df[COL_CURSO].isin(cursos_sel)
    & df[COL_GRUPO].isin(grupos_sel)
]

notas = filtrado.dropna(subset=[COL_NOTA]).copy()
notas["Resultado"] = notas[COL_NOTA].apply(lambda n: "Ganada" if n >= umbral else "Perdida")

# Nota definitiva = suma de (peso x nota) de cada estudiante, curso, grupo y corte.
# Las notas vacías cuentan como 0, igual que en tus Excel.
definitivas = (
    filtrado.assign(_p=filtrado[COL_PESO] * filtrado[COL_NOTA].fillna(0))
    .groupby([COL_CURSO, COL_GRUPO, COL_ESTUDIANTE, COL_CORTE], as_index=False)["_p"]
    .sum()
    .rename(columns={"_p": "Valor"})
)
definitivas["Resultado"] = definitivas["Valor"].apply(
    lambda v: "Ganó" if v >= umbral else "Perdió"
)

st.sidebar.divider()
st.sidebar.caption(f"Filas con los filtros actuales: {len(filtrado)} de {len(df)}")

if notas.empty:
    st.warning("No hay notas con los filtros elegidos. Cambia los filtros de la barra lateral.")
    st.stop()

# ---------------- Indicadores (solo notas definitivas) ----------------
ganaron = int((definitivas["Resultado"] == "Ganó").sum())
perdieron = int((definitivas["Resultado"] == "Perdió").sum())
total = ganaron + perdieron

CALCULOS = {
    "ganaron": lambda: ganaron,
    "perdieron": lambda: perdieron,
    "total": lambda: total,
    "promedio": lambda: f"{definitivas['Valor'].mean():.{DECIMALES}f}",
    "pct_ganaron": lambda: f"{ganaron / total * 100:.1f}%",
    "estudiantes": lambda: definitivas[COL_ESTUDIANTE].nunique(),
    "maxima": lambda: f"{definitivas['Valor'].max():.{DECIMALES}f}",
    "minima": lambda: f"{definitivas['Valor'].min():.{DECIMALES}f}",
}

st.header(SEC_KPI)
st.caption("Calculados con la nota definitiva de cada estudiante. Cada estudiante cuenta una vez por corte seleccionado.")
with st.container(key="tarjetas"):
    for col, (nombre, calculo) in zip(st.columns(len(TARJETAS)), TARJETAS):
        with col:
            with st.container(border=True):
                st.metric(nombre, CALCULOS[calculo]())

# ---------------- Resultados por curso (interactivo) ----------------
st.header(SEC_CURSO)

base_sel = st.radio(
    "¿Qué quieres contar?",
    ["Notas individuales", "Definitiva por estudiante"],
    horizontal=True,
    help="Notas individuales: cada quiz, parcial, taller... cuenta como una nota. "
    "Definitiva por estudiante: se calcula la nota final ponderada de cada estudiante "
    "en cada corte (las notas vacías cuentan como 0, igual que en tus Excel).",
)

if base_sel == "Notas individuales":
    base = notas[[COL_CURSO, COL_CORTE, COL_NOTA]].rename(columns={COL_NOTA: "Valor"})
else:
    base = definitivas.copy()
base["Resultado"] = base["Valor"].apply(lambda v: "Ganó" if v >= umbral else "Perdió")


def resumen_curso(g):
    gan = g[g["Resultado"] == "Ganó"]["Valor"]
    per = g[g["Resultado"] == "Perdió"]["Valor"]
    return pd.Series({
        "Ganaron": len(gan),
        "Perdieron": len(per),
        "Promedio de ganados": gan.mean(),
        "Promedio de perdidos": per.mean(),
        "Nota mínima": g["Valor"].min(),
        "Nota máxima": g["Valor"].max(),
    })


VISTAS = {
    "Ganaron y perdieron": ["Ganaron", "Perdieron"],
    "Promedio de ganados y perdidos": ["Promedio de ganados", "Promedio de perdidos"],
    "Nota mínima y máxima": ["Nota mínima", "Nota máxima"],
}
vista = st.selectbox("Gráfico por curso", list(VISTAS))

formatos = {
    "Ganaron": "{:.0f}",
    "Perdieron": "{:.0f}",
    "Promedio de ganados": f"{{:.{DECIMALES}f}}",
    "Promedio de perdidos": f"{{:.{DECIMALES}f}}",
    "Nota mínima": f"{{:.{DECIMALES}f}}",
    "Nota máxima": f"{{:.{DECIMALES}f}}",
}

# Una pestaña por corte: los cortes NO se suman entre sí.
cortes_disp = sorted(base[COL_CORTE].unique())
pestanas = st.tabs([f"Corte {c}" for c in cortes_disp])
for pestana, corte in zip(pestanas, cortes_disp):
    with pestana:
        tabla_curso = (
            base[base[COL_CORTE] == corte]
            .groupby(COL_CURSO)
            .apply(resumen_curso, include_groups=False)
        )
        c_tab, c_graf = st.columns([3, 2])
        with c_tab:
            with st.container(border=True):
                st.subheader(f"Tabla por curso - Corte {corte}")
                st.dataframe(
                    tabla_curso.style.format(formatos, na_rep="-"), width="stretch"
                )
        with c_graf:
            with st.container(border=True):
                st.subheader(f"{vista} - Corte {corte}")
                st.bar_chart(tabla_curso[VISTAS[vista]].fillna(0))

# ---------------- Gráficos ----------------
st.header(SEC_GRAFICOS)
for col, g in zip(st.columns(len(GRAFICOS)), GRAFICOS):
    with col:
        with st.container(border=True):
            st.subheader(g["titulo"])
            if g["tipo"] == "barras":
                datos = (
                    notas[notas["Resultado"] == "Ganada"]
                    .groupby([g["por"], COL_CORTE])
                    .size()
                    .unstack(fill_value=0)
                    .rename(columns=lambda c: f"Corte {c}")
                )
                if datos.empty:
                    st.info("No hay notas ganadas con estos filtros.")
                else:
                    st.bar_chart(datos)
            elif g["tipo"] == "lineas":
                datos = notas.pivot_table(
                    index=g["x"], columns=g["serie"], values=COL_NOTA, aggfunc="mean"
                )
                st.line_chart(datos)

# ---------------- Tabla ----------------
st.header(SEC_TABLA)
st.dataframe(filtrado, width="stretch", hide_index=True)
st.download_button(
    "⬇️ Descargar tabla filtrada (CSV)",
    filtrado.to_csv(index=False).encode("utf-8-sig"),
    file_name="notas_filtradas.csv",
    mime="text/csv",
)