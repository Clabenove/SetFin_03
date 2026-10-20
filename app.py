import os

import re

import gc

import time
import hashlib
import unicodedata

from datetime import datetime

import streamlit as st

import pandas as pd

import numpy as np

import plotly.express as px

import plotly.graph_objects as go



st.set_page_config(

    page_title="Auditoría BIM & Cumplimiento BEP - APV",

    page_icon="📋",

    layout="wide"

)



# Estilos CSS para mejorar el acabado visual y permitir exportación limpia a PDF con Ctrl+P

st.markdown("""

<style>

@media print {

    section[data-testid="stSidebar"],

    header[data-testid="stHeader"],

    div[data-testid="stToolbar"],

    .stDownloadButton,

    .stButton,

    div[data-testid="stChatInput"] {

        display: none !important;

    }

    .main .block-container {

        padding-top: 0.5rem !important;

        max-width: 100% !important;

    }

}

.kpi-card {

    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);

    border: 1px solid #334155;

    border-radius: 10px;

    padding: 16px;

    text-align: center;

    box-shadow: 0 4px 6px rgba(0,0,0,0.2);

}

.kpi-title {

    font-size: 0.85rem;

    color: #94a3b8;

    text-transform: uppercase;

    letter-spacing: 0.05em;

    margin-bottom: 6px;

}

.kpi-value {

    font-size: 1.75rem;

    font-weight: 700;

    color: #f8fafc;

}

.kpi-sub {

    font-size: 0.8rem;

    color: #38bdf8;

    margin-top: 4px;

}

</style>

""", unsafe_allow_html=True)



st.title("📋 Dashboard Integral de Auditoría BIM - APV")

st.info("**Alcance de auditoría:** se evalúan únicamente propiedades APV encontradas en el Parquet consolidado (datos exportados). Los campos que no se exportaron no cuentan como vacíos. El BCF sirve para registrar/comunicar incidencias; la comprobación de valores se hace sobre las propiedades exportadas, no sobre el BCF por sí solo.")



PARAMETROS_APV = list(dict.fromkeys([

    "01_01_APV_PROYECTO", "01_02_APV_FASE",

    "01_03_APV_ESTADO", "01_04_APV_TIPOLOGIA",

    "01_05_APV_DISCIPLINA", "01_06_APV_SUBDISCIPLINA",

    "01_07_APV_ELEMENTO", "01_08_APV_CLASIFICACION",

    "01_09_APV_NOMBRE", "01_10_APV_ALINEACION",

    "01_11_APV_NUMERO", "01_12_APV_MATERIAL",

    "01_13_APV_CAD", "01_14_APV_ZONA",

    "02_01_APV_CAPITULO", "02_02_APV_SUBCAPITULO-1",

    "02_03_APV_SUBCAPITULO-2", "02_04_01_APV_MEDICION",

    "02_04_02_APV_MEDICION-ASOC-1", "02_04_03_APV_MEDICION-ASOC-2",

    "02_04_04_APV_MEDICION-ASOC-3", "02_05_01_APV_UNIDAD-OBRA",

    "02_05_02_APV_UO-ASOC-1", "02_05_03_APV_UO-ASOC-2",

    "02_05_04_APV_UO-ASOC-3", "02_06_01_APV_TIPO-MED",

    "02_06_02_APV_TM-ASOC-1", "02_06_03_APV_TM-ASOC-2",

    "02_06_04_APV_TM-ASOC-3", "03_01_APV_FASE-OBRA",

    "03_02_APV_PLANOS", "03_03_APV_PPTP",

    "03_04_APV_CALIDAD-MOD", "04_01_APV_CÓDIGO-TAREA",

    "04_02_APV_NOMBRE-TAREA", "04_03_APV_INICIO-EJECUCION",

    "04_04_APV_FIN-EJECUCION", "04_05_APV_PLAN-REF",

    "04_06_APV_CERTIF-REF", "04_07_APV_CERTIF",

    "04_08_APV_PORCENTAJE-EJECUTADO", "04_09_APV_CERTIF-MED",

    "04_10_APV_CERTIF-MED-ASOC-1", "04_11_APV_CERTIF-MED-ASOC-2",

    "04_12_APV_CERTIF-MED-ASOC-3", "05_01_APV_SEG-SALUD",

    "05_02_APV_INFORMES-APROBACION", "05_03_APV_CONTROL-CALIDAD",

    "05_03_01_APV_COD-TRAZ", "05_04_APV_ENSAYOS",

    "05_05_APV_FOTOGRAFIAS", "05_06_APV_MEDIO-AMBIENTE",

    "05_07_APV_GESTION-RESIDUOS", "05_08_APV_SERV-AFECTADOS",

    "06_01_APV_PRY-LIQUIDACION", "06_02_APV_LIBRO-EDIF",

    "07_01_APV_CAPA-GIS", "07_02_APV_CAMPO-1",

    "07_03_APV_CAMPO-2", "07_04_APV_CAMPO-3",

    "07_05_APV_CAMPO-4", "07_06_APV_CAMPO-5",

    "07_07_APV_CAMPO-6", "07_08_APV_CAMPO-7",

    "07_09_APV_CAMPO-8", "07_10_APV_CAMPO-9",

    "07_11_APV_CAMPO-10", "07_12_APV_CAMPO-N",

    "08_01_APV_PLAN-MANTENIMIENTO", "08_02_APV_MANUALES-FICHAS",

    "08_03_APV_COD-MANTENIMIENTO", "08_04_APV_COD-EXPLOTACION",

    "08_05_APV_AUX-EXPLOTACION", "08_06_APV_COD-CONTABLE",

    "08_07_APV_CAP-CONTABLE", "08_08_APV_SUB-CAP-CONTABLE",

    "09-02_00_APV_PROYECTO", "09-02_01_APV_SONDEO",

    "09-02_02_APV_COTA-MUESTRA(m)", "09-02_03_APV_DESC-ESTRATO",

    "09-02_04_APV_TIPO", "09-02_05_APV_NÚMERO MUESTRA",

    "09-03_01_APV_PASA-100 (%)", "09-03_02_APV_PASA-80 (%)",

    "09-03_03_APV_PASA-63 (%)", "09-03_04_APV_PASA-50 (%)",

    "09-03_05_APV_PASA-40 (%)", "09-03_06_APV_PASA-25 (%)",

    "09-03_07_APV_PASA-20 (%)", "09-03_08_APV_PASA-12,5 (%)",

    "09-03_09_APV_PASA-10 (%)", "09-03_10_APV_PASA-6,3 (%)",

    "09-03_11_APV_PASA-5 (%)", "09-03_12_APV_PASA-2 (%)",

    "09-03_13_APV_PASA-1,25 (%)", "09-03_14_APV_PASA-0,4 (%)",

    "09-03_15_APV_PASA-0,16 (%)", "09-03_16_APV_PASA-0,08 (%)",

    "09-03_17_APV_ATTERBERG-LL", "09-03_18_APV_ATTERBERG-LP",

    "09-03_19_APV_ATTERBERG-IP", "09-03_20_APV_HN (%)",

    "09-03_21_APV_DENS-APAR-HUMEDA (g/cm3)",

    "09-03_22_APV_DENS-APAR-SECA (g/cm3)",

    "09-03_23_APV_DENS-APAR-SECA (g/cm3)",

    "09-04_01_APV_ACIDEZ BG (ml/Kg)", "09-04_02_APV_SULFATOS (mg/Kg)",

    "09-04_03_APV_CARBONATOS (mg/Kg)", "09-04_04_APV_YESO (%SO4CaH2O)",

    "09-04_05_APV_SALES SOLUBLES", "09-04_06_APV_MAT ORGANICA (%)",

    "09-05_01_APV_CS (kPa)", "09-05_02_APV_CU (MPa)",

    "09-05_03_APV_BRASILEÑO (MPa)", "09-05_04_APV_FRANKLIN (Mpa)",

    "09-05_05_APV_CORTE DIRECTO-c(kPa)", "09-05_06_APV_CORTE DIRECTO-fi(°)",

    "09-05_07_APV_TRIAXIAL-c(kPa)", "09-05_08_APV_TRIAXIAL-fi(°)",

    "09-05_09_APV_EDOMETRO-Cc", "09-05_10_APV_EDOMETRO-Cs",

    "09-05_11_APV_EDOMETRO-e0", "09-05_12_APV_EDOMETRO-sigma'p (Kg/cm2)",

    "09-05_13_APV_EDOMETRO-Cv (m2/año)",

    "09-05_14_APV_LAMBE-HINCHAMIENTO (Mpa)",

    "09-05_15_APV_LAMBE-CAMBIO-POT-VOL",

    "09-05_16_APV_DENSIDAD-MAX(g/cm3)", "09-05_17_APV_DENSIDAD-MIN(g/cm3)",

    "09-05_18_APV_INDICE-COLAPSO (%)", "09-06_01_APV_LEFRANC-PERMEAB (%)",

    "09-07_01_APV_CO2-LIBRE (mg/l)", "09-07_02_APV_ACIDEZ (ud PH)",

    "09-07_03_APV_AMONIO (mg/l)", "09-07_04_APV_MAGNESIO (mg/l)",

    "09-07_05_APV_SULFATOS (mg/l)", "09-07_06_APV_RESIDUO SECO (mg/l)",

    "10_01_APV_ENLACE A FOTO", "10_02_APV_FECHA", "10_03_APV_DISCIPLINA"

]))



PARAMS_NO_GEO = [p for p in PARAMETROS_APV if not p.startswith("09")]

PARAMS_GEO = [p for p in PARAMETROS_APV if p.startswith("09")]



NOMBRES_GRUPOS_BEP = {

    "01": "01. Identificación y Clasificación",

    "02": "02. Mediciones y Presupuesto (5D)",

    "03": "03. Documentación y Calidad",

    "04": "04. Planificación y Certificación (4D)",

    "05": "05. Seguridad, Calidad y Medio Ambiente",

    "06": "06. Liquidación y Libro del Edificio",

    "07": "07. Integración GIS",

    "08": "08. Mantenimiento y Explotación (6D)",

    "09": "09. Geotecnia y Ensayos",

    "10": "10. Seguimiento Fotográfico"

}



VACIOS_EXACTOS = [
    "", " ", "  ", "nan", "NaN", "NAN",
    "none", "None", "NONE", "<na>", "<NA>", "null", "NULL"
]

# El guion es un comodín válido del BEP y NO se considera vacío.
COMODINES_EXACTOS = ["-", " -", "- ", " - "]
VALORES_VACIOS_LOWER = {"", "nan", "none", "<na>", "null", "nat"}
COL_PCT_CUMPLIMIENTO = "% Cumplimiento (Dato + '-')"


def _normalizar_serie_texto(serie):
    """Normaliza espacios Unicode invisibles y mayúsculas para comparar valores."""
    texto = serie.astype("string")
    texto = texto.str.replace("\u00a0", " ", regex=False)
    texto = texto.str.replace("\u200b", "", regex=False)
    texto = texto.str.replace("\ufeff", "", regex=False)
    return texto.str.strip().str.lower()


def mascara_vacio_serie(serie):
    """Máscara de vacíos real: nulos, celdas en blanco y marcadores de nulo comunes."""
    normalizada = _normalizar_serie_texto(serie)
    return (serie.isna() | normalizada.isin(VALORES_VACIOS_LOWER)).to_numpy(dtype=bool)


def es_valor_vacio(valor):
    """Versión escalar de la regla de vacíos; conserva 0, False y el guion como datos."""
    try:
        if pd.isna(valor):
            return True
    except (TypeError, ValueError):
        pass
    texto = unicodedata.normalize("NFKC", str(valor))
    texto = texto.replace("\u00a0", " ").replace("\u200b", "").replace("\ufeff", "")
    return texto.strip().lower() in VALORES_VACIOS_LOWER


def mascara_vacio_rapida(df_ref, col_name):
    """Devuelve vacíos solo si el parámetro existe; un nombre no localizado no es un vacío."""
    if col_name not in df_ref.columns:
        # Evita convertir un campo ausente en cientos de miles de falsas alertas.
        return np.zeros(len(df_ref), dtype=bool)
    return mascara_vacio_serie(df_ref[col_name])


def mascara_comodin_rapida(df_ref, col_name):
    """Detecta el comodín BEP '-' tolerando espacios alrededor del guion."""
    if col_name not in df_ref.columns:
        return np.zeros(len(df_ref), dtype=bool)
    return (_normalizar_serie_texto(df_ref[col_name]) == "-").fillna(False).to_numpy(dtype=bool)


def normalizar_nombre_columna(nombre):
    """Normaliza columnas ignorando acentos y separadores del nombre."""
    texto = unicodedata.normalize("NFKD", str(nombre))
    texto = texto.encode("ascii", "ignore").decode("ascii").lower()
    return re.sub(r"[^a-z0-9]+", "", texto)


def coalescer_series(series_list):
    """Une columnas equivalentes usando el primer valor real disponible por fila."""
    if not series_list:
        return pd.Series(dtype="object")
    base = series_list[0].copy()
    for candidata in series_list[1:]:
        posiciones = np.flatnonzero(mascara_vacio_serie(base))
        if len(posiciones):
            # object evita errores al unir categorías o tipos distintos del Parquet.
            base = base.astype(object)
            base.iloc[posiciones] = candidata.iloc[posiciones].to_numpy()
    return base


def coalescer_columnas_duplicadas(df):
    """No descarta duplicados: combina sus valores en la columna que se conserva."""
    if not df.columns.duplicated().any():
        return df
    posiciones_por_nombre = {}
    for i, nombre in enumerate(df.columns):
        posiciones_por_nombre.setdefault(nombre, []).append(i)
    columnas = {}
    for nombre, posiciones in posiciones_por_nombre.items():
        columnas[nombre] = coalescer_series([df.iloc[:, i] for i in posiciones])
    return pd.DataFrame(columnas, index=df.index)


def resolver_parametros_apv(df):
    """Mapea parámetros oficiales a columnas equivalentes en el Parquet.

    Admite prefijos como Pset_APV, diferencias de acentos, espacios y separadores.
    Si encuentra varias columnas equivalentes, fusiona los valores por fila.
    """
    columnas_origen = list(df.columns)
    normalizadas = {c: normalizar_nombre_columna(c) for c in columnas_origen}

    def clave_sin_codigo(parametro):
        # Ej.: 01_01_APV_PROYECTO -> APV_PROYECTO; 09-02_00_APV_TIPO -> APV_TIPO.
        resto = re.sub(r"^\d+(?:[-_]\d+)*[-_]*", "", str(parametro))
        return normalizar_nombre_columna(resto)

    claves_sin_codigo = {p: clave_sin_codigo(p) for p in PARAMETROS_APV}
    frecuencia_clave = {}
    for p, clave_tail in claves_sin_codigo.items():
        frecuencia_clave[clave_tail] = frecuencia_clave.get(clave_tail, 0) + 1

    mapa = {}
    for parametro in PARAMETROS_APV:
        clave = normalizar_nombre_columna(parametro)
        # Solo se considera exportado si hay una columna fuente cuyo nombre
        # contiene el nombre normalizado completo del parámetro oficial.
        # Se admite un prefijo externo (p. ej. nombre de Pset), pero no
        # coincidencias parciales ni similitud difusa.
        candidatas = [
            c for c in columnas_origen
            if normalizadas[c] == clave or normalizadas[c].endswith(clave)
        ]

        # Algunos exportadores omiten el código BEP y dejan solo el nombre
        # de propiedad (p. ej. APV_PROYECTO). Solo se acepta si ese nombre
        # sin código es único entre los parámetros oficiales.
        clave_tail = claves_sin_codigo[parametro]
        if not candidatas and frecuencia_clave.get(clave_tail, 0) == 1:
            candidatas = [
                c for c in columnas_origen
                if normalizadas[c] == clave_tail or normalizadas[c].endswith(clave_tail)
            ]

        if not candidatas:
            continue
        candidatas.sort(key=lambda c: (normalizadas[c] != clave, len(normalizadas[c]), str(c)))
        df[parametro] = coalescer_series([df[c] for c in candidatas])
        mapa[parametro] = candidatas
    return df, mapa


def diagnosticar_nombre_bep(nombre_archivo):

    if not str(nombre_archivo).lower().endswith(".ifc"):

        return "❌ No tiene extensión .ifc"

    base = str(nombre_archivo)[:-4]

    partes = base.split("_")

    if len(partes) != 7:

        return (

            f"❌ Estructura incorrecta: tiene {len(partes)} "

            "bloques separados por '_' (se esperan 7)"

        )

    puerto, contrato, fase, tipo, disc, desc, rev = partes

    errores = []

    if puerto.upper() not in ["V", "S", "G"]:

        errores.append(f"Bloque 1 Puerto ('{puerto}'): debe ser V, S o G")

    if contrato.upper() != "N035":

        if contrato.upper() == "NO35":

            errores.append(

                "Bloque 2 Contrato ('NO35'): tiene letra 'O' en lugar "

                "del número '0' (debe ser N035)"

            )

        else:

            errores.append(f"Bloque 2 Contrato ('{contrato}'): debe ser 'N035'")

    if fase.upper() != "OB":

        if fase == "0B":

            errores.append(

                "Bloque 3 Fase ('0B'): tiene un cero '0' en vez "

                "de la letra 'O' (debe ser 'OB')"

            )

        else:

            errores.append(f"Bloque 3 Fase ('{fase}'): debe ser 'OB'")

    if not re.match(r"^[A-Za-z]{3}$", tipo):

        errores.append(

            f"Bloque 4 Tipo ('{tipo}'): debe tener 3 letras (ej. MOD, SEG)"

        )

    if not re.match(r"^[A-Za-z]{3}$", disc):

        errores.append(f"Bloque 5 Disciplina ('{disc}'): debe tener 3 letras")

    if not re.match(r"^[A-Za-z0-9\-]+$", desc):

        errores.append(f"Bloque 6 Descripción ('{desc}'): caracteres inválidos")

    if not re.match(r"^\d{2}[A-Za-z]$", rev):

        errores.append(

            f"Bloque 7 Revisión ('{rev}'): debe ser 2 dígitos + 1 letra"

        )

    if not errores:

        return "✅ Cumple patrón BEP"

    return "❌ No cumple: " + " | ".join(errores)





def sugerir_nombre_bep(nombre_archivo):

    if not str(nombre_archivo).lower().endswith(".ifc"):

        return "V_N035_OB_MOD_EST_Proyecto_01A.ifc"

    base = str(nombre_archivo)[:-4]

    partes = base.split("_")

    puerto = partes[0] if len(partes) > 0 and partes[0].upper() in ["V", "S", "G"] else "V"

    contrato = "N035"

    fase = "OB"

    tipo = partes[3] if len(partes) > 3 and re.match(r"^[A-Za-z]{3}$", partes[3]) else "MOD"

    disc = partes[4] if len(partes) > 4 and re.match(r"^[A-Za-z]{3}$", partes[4]) else "EST"

    desc = re.sub(r"[^A-Za-z0-9\-]", "", partes[5]) if len(partes) > 5 else "Proyecto"

    if not desc:

        desc = "Proyecto"

    rev = partes[6] if len(partes) > 6 and re.match(r"^\d{2}[A-Za-z]$", partes[6]) else "01A"

    return f"{puerto.upper()}_{contrato}_{fase}_{tipo.upper()}_{disc.upper()}_{desc}_{rev.upper()}.ifc"





def generar_xml_navisworks(

    valores_unicos,

    nombre_set="Auditoria_APV_Elementos_Vacios",

    usar_id_nativo=False

):

    schema_url = (

        "http://download.autodesk.com/us/navisworks/schemas/"

        "nw-exchange-12.0.xsd"

    )

    prop_name = "Id" if usar_id_nativo else "GlobalId"

    xml = '<?xml version="1.0" encoding="UTF-8" ?>\n'

    xml += (

        '<exchange xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '

        f'xsi:noNamespaceSchemaLocation="{schema_url}" units="m">\n'

    )

    xml += '  <selectionsets>\n'

    xml += f'    <selectionset name="{nombre_set}">\n'

    xml += '      <findspec mode="some" disjoint="0">\n'

    xml += '        <conditions>\n'

    for val in valores_unicos[:1000]:

        xml += '          <condition test="equals" flags="10">\n'

        xml += f'            <property><name>{prop_name}</name></property>\n'

        xml += f'            <value><data type="wstring">{val}</data></value>\n'

        xml += '          </condition>\n'

    xml += '        </conditions>\n'

    xml += '        <locator>/</locator>\n'

    xml += '      </findspec>\n'

    xml += '    </selectionset>\n'

    xml += '  </selectionsets>\n'

    xml += '</exchange>'

    return xml





def generar_ifc_matriz_auditoria(df_matriz, fecha_emision):
    """Genera un IFC4 de informe, con una caja esquemática por modelo y sus métricas como propiedades.

    IMPORTANTE: la geometría de las cajas es solo representativa del registro de auditoría;
    no reproduce la geometría original de los modelos IFC auditados.
    """
    try:
        import tempfile
        import ifcopenshell.api
    except Exception as exc:
        raise RuntimeError(
            "No se pudo cargar IfcOpenShell. Comprueba que 'ifcopenshell' esté en requirements.txt "
            "y que Streamlit Cloud haya terminado de instalar las dependencias."
        ) from exc

    if df_matriz is None or df_matriz.empty:
        raise ValueError("No hay modelos en la matriz para exportar a IFC.")

    run = ifcopenshell.api.run
    model = run("project.create_file", version="IFC4")
    proyecto = run(
        "root.create_entity", model,
        ifc_class="IfcProject",
        name="APV - Informe de Auditoría BIM y Cumplimiento BEP"
    )
    unidades = run("unit.assign_unit", model)
    contexto_modelo = run("context.add_context", model, context_type="Model")
    contexto_cuerpo = run(
        "context.add_context", model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=contexto_modelo
    )
    proyecto.RepresentationContexts = [contexto_modelo]
    if unidades is not None:
        proyecto.UnitsInContext = unidades

    site = run("root.create_entity", model, ifc_class="IfcSite", name="APV - Auditoría")
    edificio = run("root.create_entity", model, ifc_class="IfcBuilding", name="Informe de Calidad IFC")
    planta = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Registros de Modelos")
    run("aggregate.assign_object", model, products=[site], relating_object=proyecto)
    run("aggregate.assign_object", model, products=[edificio], relating_object=site)
    run("aggregate.assign_object", model, products=[planta], relating_object=edificio)

    def punto3(coords):
        return model.create_entity("IfcCartesianPoint", Coordinates=tuple(float(v) for v in coords))

    eje_z = model.create_entity("IfcDirection", DirectionRatios=(0.0, 0.0, 1.0))
    eje_x = model.create_entity("IfcDirection", DirectionRatios=(1.0, 0.0, 0.0))

    def axis3(coords):
        return model.create_entity(
            "IfcAxis2Placement3D",
            Location=punto3(coords),
            Axis=eje_z,
            RefDirection=eje_x
        )

    def colocacion(parent, coords):
        return model.create_entity(
            "IfcLocalPlacement",
            PlacementRelTo=parent,
            RelativePlacement=axis3(coords)
        )

    site.ObjectPlacement = colocacion(None, (0.0, 0.0, 0.0))
    edificio.ObjectPlacement = colocacion(site.ObjectPlacement, (0.0, 0.0, 0.0))
    planta.ObjectPlacement = colocacion(edificio.ObjectPlacement, (0.0, 0.0, 0.0))

    # Caja sencilla por modelo: permite seleccionar el registro en Navisworks y consultar sus propiedades.
    perfil = model.create_entity(
        "IfcRectangleProfileDef",
        ProfileType="AREA",
        ProfileName="Caja esquemática de registro de auditoría",
        XDim=1500.0,
        YDim=1500.0
    )
    proxies = []

    def valor_ifc(valor):
        if valor is None:
            return None
        try:
            if pd.isna(valor):
                return None
        except (TypeError, ValueError):
            pass
        if isinstance(valor, np.generic):
            valor = valor.item()
        if isinstance(valor, float) and not np.isfinite(valor):
            return None
        if isinstance(valor, (str, int, float, bool)):
            texto = str(valor).strip() if isinstance(valor, str) else None
            if isinstance(valor, str) and texto.lower() in {"", "nan", "none", "<na>", "null"}:
                return None
            return valor[:1500] if isinstance(valor, str) else valor
        return str(valor)[:1500]

    def nombre_propiedad(nombre):
        limpio = unicodedata.normalize("NFKD", str(nombre)).encode("ascii", "ignore").decode("ascii")
        limpio = re.sub(r"[^A-Za-z0-9_]+", "_", limpio).strip("_")
        if not limpio:
            limpio = "Propiedad"
        if limpio[0].isdigit():
            limpio = "P_" + limpio
        return limpio[:80]

    for indice, (_, fila) in enumerate(df_matriz.reset_index(drop=True).iterrows()):
        archivo = str(fila.get("Archivo_Origen", f"Modelo_{indice + 1}"))
        proxy = run(
            "root.create_entity", model,
            ifc_class="IfcBuildingElementProxy",
            name=archivo
        )
        proxy.Description = "Registro esquemático de calidad; no representa la geometría original del modelo."
        proxy.ObjectType = "Registro de auditoría APV"
        proxy.Tag = f"APV_AUDIT_{indice + 1:04d}"
        # Orden en cuadrícula para que los registros sean visibles y seleccionables en Navisworks.
        # El proyecto usa unidades de longitud IFC en milímetros por defecto.
        x = float((indice % 10) * 3000)
        y = float((indice // 10) * 3000)
        proxy.ObjectPlacement = colocacion(planta.ObjectPlacement, (x, y, 0.0))

        posicion_solido = axis3((0.0, 0.0, 0.0))
        solido = model.create_entity(
            "IfcExtrudedAreaSolid",
            SweptArea=perfil,
            Position=posicion_solido,
            ExtrudedDirection=eje_z,
            Depth=500.0
        )
        representacion = model.create_entity(
            "IfcShapeRepresentation",
            ContextOfItems=contexto_cuerpo,
            RepresentationIdentifier="Body",
            RepresentationType="SweptSolid",
            Items=[solido]
        )
        proxy.Representation = model.create_entity(
            "IfcProductDefinitionShape",
            Name=None,
            Description=None,
            Representations=[representacion]
        )

        propiedades = {}
        for columna, valor in fila.items():
            v = valor_ifc(valor)
            if v is None:
                continue
            clave = nombre_propiedad(columna)
            if clave not in propiedades:
                propiedades[clave] = v
        propiedades["Fecha_Emision_Informe"] = str(fecha_emision)
        propiedades["Tipo_Archivo"] = "IFC4 - Informe de auditoría, no modelo de diseño"
        propiedades["Nota_Geometria"] = "Caja esquemática del registro; no es la geometría original del modelo IFC."

        pset = run(
            "pset.add_pset", model,
            product=proxy,
            name="APV_AuditoriaCalidadModelo"
        )
        run("pset.edit_pset", model, pset=pset, properties=propiedades)
        proxies.append(proxy)

    if proxies:
        run("spatial.assign_container", model, relating_structure=planta, products=proxies)

    # Volvemos bytes el IFC generado sin dejar ficheros temporales en el servidor.
    with tempfile.TemporaryDirectory() as carpeta_tmp:
        ruta_ifc = os.path.join(carpeta_tmp, "Matriz_Ejecutiva_Calidad_Modelos_APV.ifc")
        model.write(ruta_ifc)
        with open(ruta_ifc, "rb") as archivo_ifc:
            return archivo_ifc.read()


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RUTA_PARQUET = os.path.join(BASE_DIR, "resumen_ifc_consolidado.parquet")



if not os.path.isfile(RUTA_PARQUET):

    st.error(f"No se encuentra el archivo: {RUTA_PARQUET}")

    st.stop()





@st.cache_resource(show_spinner="Cargando e indexando base de datos BIM...")
def inicializar_motor_apv(ruta, tamano_archivo, mtime_ns):
    """Carga la base, resuelve alias APV y precalcula solo campos verificables.

    tamano_archivo y mtime_ns forman parte de la clave de caché; así un Parquet
    actualizado en la misma ruta no conserva resultados obsoletos.
    """
    t0 = time.perf_counter()
    print("[DIAG 1] Leyendo archivo Parquet...", flush=True)
    df_raw = pd.read_parquet(ruta, engine="pyarrow")
    # Algunos Parquet exportados pueden contener etiquetas repetidas (por ejemplo,
    # dos columnas GlobalId). Se fusionan por fila antes del mapeo APV.
    df_raw = coalescer_columnas_duplicadas(df_raw)
    df_raw, mapa_parametros = resolver_parametros_apv(df_raw)
    # Segunda barrera defensiva: las fases siguientes deben trabajar con nombres únicos.
    df_raw = coalescer_columnas_duplicadas(df_raw)
    if df_raw.columns.duplicated().any():
        raise ValueError("No se pudieron normalizar los nombres duplicados de columnas del Parquet.")

    if "Archivo_Origen" not in df_raw.columns:
        raise ValueError("El Parquet no contiene la columna obligatoria 'Archivo_Origen'.")

    n_filas = len(df_raw)
    print(
        f"[DIAG 2] Parquet cargado: {n_filas:,} filas x "
        f"{len(df_raw.columns)} cols en {time.perf_counter() - t0:.2f}s",
        flush=True
    )

    archivos_unicos = sorted(df_raw["Archivo_Origen"].dropna().unique().tolist())
    s_arch = df_raw["Archivo_Origen"]
    params_no_geo_localizados = [p for p in PARAMS_NO_GEO if p in mapa_parametros]
    params_geo_localizados = [p for p in PARAMS_GEO if p in mapa_parametros]
    parametros_con_dato_por_archivo = {a: set() for a in archivos_unicos}
    celdas_con_dato_por_archivo = {a: 0 for a in archivos_unicos}
    filas_con_dato_parametro = {}

    pres_base = np.zeros(n_filas, dtype=np.uint16)
    vac_base = np.zeros(n_filas, dtype=np.uint16)
    pres_geo = np.zeros(n_filas, dtype=np.uint16)
    vac_geo = np.zeros(n_filas, dtype=np.uint16)

    # Los parámetros ausentes de la exportación no participan en el cómputo de vacíos.
    for col in params_no_geo_localizados + params_geo_localizados:
        v = mascara_vacio_rapida(df_raw, col)
        filas_con_dato_parametro[col] = int((~v).sum())
        if col in params_no_geo_localizados:
            vac_base += v.astype(np.uint16)
            pres_base += (~v).astype(np.uint16)
        else:
            vac_geo += v.astype(np.uint16)
            pres_geo += (~v).astype(np.uint16)
        if not v.all():
            archivos_con_valor = s_arch.loc[~v].dropna().value_counts()
            for archivo, cantidad in archivos_con_valor.items():
                if archivo in parametros_con_dato_por_archivo:
                    parametros_con_dato_por_archivo[archivo].add(col)
                    celdas_con_dato_por_archivo[archivo] += int(cantidad)

    pres_all = pres_base + pres_geo
    vac_all = vac_base + vac_geo

    print("[DIAG 3] Precalculando grupos APV por modelo...", flush=True)
    cols_apv_en_df = [c for c in df_raw.columns if "APV" in str(c).upper()]
    grupos_por_arch = {a: set() for a in archivos_unicos}
    for c in cols_apv_en_df:
        prefijo = str(c).split("_")[0] if "_" in str(c) else ""
        v = mascara_vacio_rapida(df_raw, c)
        if not v.all():
            for archivo in s_arch.loc[~v].dropna().unique():
                if archivo in grupos_por_arch:
                    grupos_por_arch[archivo].add(prefijo)

    info_grupos = []
    info_modelos = []
    for arch in archivos_unicos:
        es_geo = "geo" in str(arch).lower()
        g_set = grupos_por_arch[arch]
        params_con_dato = sorted(parametros_con_dato_por_archivo[arch])
        params_sin_dato = sorted(set(mapa_parametros) - set(params_con_dato))
        info_grupos.append({
            "Archivo IFC": arch,
            "Tipo de Modelo": "Modelo de Geotecnia" if es_geo else "Modelo Estándar / Proyecto",
            "Grupos Teóricos (BEP)": 11 if es_geo else 9,
            "Grupos Totales Detectados": len(g_set),
            "Grupos Específicos Detectados": ", ".join(sorted(list(g_set))) if g_set else "Ninguno"
        })
        n_filas_arch = int((s_arch == arch).sum())
        info_modelos.append({
            "Archivo IFC": arch,
            "Filas en Parquet": n_filas_arch,
            "Parámetros APV con algún dato": len(params_con_dato),
            "Parámetros APV detectados con dato": ", ".join(params_con_dato[:25]) + (" …" if len(params_con_dato) > 25 else "") if params_con_dato else "Ninguno localizado con datos",
            "Parámetros APV sin dato extraído": ", ".join(params_sin_dato[:25]) + (" …" if len(params_sin_dato) > 25 else "") if params_sin_dato else "Ninguno",
            "Celdas APV con dato en este modelo": celdas_con_dato_por_archivo[arch]
        })

    df_grupos = pd.DataFrame(info_grupos, columns=[
        "Archivo IFC", "Tipo de Modelo", "Grupos Teóricos (BEP)",
        "Grupos Totales Detectados", "Grupos Específicos Detectados"
    ])
    df_diagnostico_modelos = pd.DataFrame(info_modelos, columns=[
        "Archivo IFC", "Filas en Parquet", "Parámetros APV con algún dato",
        "Parámetros APV detectados con dato", "Parámetros APV sin dato extraído",
        "Celdas APV con dato en este modelo"
    ])
    info_mapa = []
    for parametro in PARAMETROS_APV:
        cols_origen = mapa_parametros.get(parametro, [])
        info_mapa.append({
            "Parámetro APV oficial": parametro,
            "Estado de lectura": "✅ Localizado" if cols_origen else "⚪ No localizado en el Parquet",
            "Columna(s) origen usada(s)": " | ".join(map(str, cols_origen)) if cols_origen else "",
            "Filas con valor no vacío": filas_con_dato_parametro.get(parametro, 0)
        })
    df_mapa_parametros = pd.DataFrame(info_mapa)

    gc.collect()
    print(
        f"[DIAG 4] Parámetros localizados: {len(mapa_parametros)}/{len(PARAMETROS_APV)}. "
        f"Motor completado en {time.perf_counter() - t0:.2f}s",
        flush=True
    )
    return (
        df_raw, archivos_unicos, df_grupos,
        pres_base, vac_base, pres_all, vac_all,
        mapa_parametros, df_mapa_parametros, df_diagnostico_modelos,
        parametros_con_dato_por_archivo
    )


_parquet_stat = os.stat(RUTA_PARQUET)
(
    df_original, archivos_disp, df_informe_grupos,
    pres_base_arr, vac_base_arr, pres_all_arr, vac_all_arr,
    mapa_parametros_apv, df_mapa_parametros_apv, df_diagnostico_modelos_apv,
    parametros_con_dato_por_archivo_apv
) = inicializar_motor_apv(RUTA_PARQUET, _parquet_stat.st_size, _parquet_stat.st_mtime_ns)

PARAMETROS_LOCALIZADOS = [p for p in PARAMETROS_APV if p in mapa_parametros_apv]
PARAMETROS_NO_LOCALIZADOS = [p for p in PARAMETROS_APV if p not in mapa_parametros_apv]
PARAMS_NO_GEO_LOCALIZADOS = [p for p in PARAMS_NO_GEO if p in mapa_parametros_apv]
PARAMS_GEO_LOCALIZADOS = [p for p in PARAMS_GEO if p in mapa_parametros_apv]

# Diagnóstico visible: evita confundir un campo no exportado con un parámetro vacío.
with st.expander(
    f"🔎 Diagnóstico de exportación: {len(PARAMETROS_LOCALIZADOS)} parámetros encontrados en el Parquet",
    expanded=False
):
    st.markdown(
        "El dashboard solo calcula incumplimientos con parámetros que ha podido localizar "
        "en el Parquet. Los campos no encontrados se muestran como **no localizados** y "
        "no se cuentan como celdas vacías. Si un valor se ve en Navisworks pero no aparece "
        "en esta tabla, hay que revisar la exportación/consolidación de la base."
    )
    st.dataframe(
        df_mapa_parametros_apv[df_mapa_parametros_apv["Estado de lectura"] == "✅ Localizado"],
        width="stretch", hide_index=True
    )
    st.success(
        "La auditoría solo puntúa parámetros localizados en las columnas fuente del Parquet. "
        "Los parámetros no exportados no se suman al denominador ni se marcan como vacíos."
    )
    mostrar_no_exportados = st.checkbox(
        "Mostrar también parámetros oficiales que NO se encontraron en la exportación (solo diagnóstico)",
        value=False,
        key="mostrar_parametros_no_exportados"
    )
    if mostrar_no_exportados and PARAMETROS_NO_LOCALIZADOS:
        st.dataframe(
            df_mapa_parametros_apv[df_mapa_parametros_apv["Estado de lectura"] != "✅ Localizado"],
            width="stretch", hide_index=True
        )
    st.markdown("#### Diagnóstico por modelo IFC")
    st.dataframe(df_diagnostico_modelos_apv, width="stretch", hide_index=True)
    m_codrag_diag = df_diagnostico_modelos_apv["Archivo IFC"].astype(str).str.contains(
        "CoDrag2VLC", case=False, regex=False, na=False
    )
    if m_codrag_diag.any():
        st.markdown("#### Revisión específica de CoDrag2VLC")
        st.dataframe(df_diagnostico_modelos_apv.loc[m_codrag_diag], width="stretch", hide_index=True)
        for archivo_codrag in df_diagnostico_modelos_apv.loc[m_codrag_diag, "Archivo IFC"].astype(str):
            params_con_dato_codrag = sorted(parametros_con_dato_por_archivo_apv.get(archivo_codrag, set()))
            params_sin_dato_codrag = sorted(set(mapa_parametros_apv) - set(params_con_dato_codrag))
            with st.expander(f"Detalle completo de parámetros extraídos: {archivo_codrag}"):
                st.write(f"**Con al menos un valor en el Parquet ({len(params_con_dato_codrag)}):**")
                st.code("\n".join(params_con_dato_codrag) if params_con_dato_codrag else "Ninguno")
                st.write(f"**Sin ningún valor extraído en las filas de este modelo ({len(params_sin_dato_codrag)}):**")
                st.code("\n".join(params_sin_dato_codrag) if params_sin_dato_codrag else "Ninguno")
                st.caption(
                    "Que un parámetro esté en la segunda lista no demuestra que esté vacío en Navisworks: "
                    "significa que no se encontró ningún valor de ese campo en el Parquet para este IFC. "
                    "Por eso no se califica como incumplimiento automático."
                )
    else:
        st.info(
            "No aparece el texto 'CoDrag2VLC' en la columna Archivo_Origen del Parquet. "
            "Revisa el nombre exacto con el que el modelo se consolidó en la base."
        )


col_id_nativo = (

    "ID_Elemento" if "ID_Elemento" in df_original.columns else "GlobalId"

)



# --- BARRA LATERAL ---

st.sidebar.header("⚙ Filtros de Auditoría")

incluir_geo = st.sidebar.checkbox("Incluir Psets 09 (Geotecnia)", value=False)

params_auditar = PARAMETROS_LOCALIZADOS if incluir_geo else PARAMS_NO_GEO_LOCALIZADOS
st.sidebar.caption(
    f"Alcance: {len(params_auditar)} parámetros realmente encontrados en la exportación. "
    "Los parámetros que no se exportaron quedan fuera del cálculo de cumplimiento."
)



ocultar_fantasmas = st.sidebar.checkbox(

    "Omitir sub-elementos fantasma (sin ningún Pset APV)", value=True

)

unificar_duplicados = st.sidebar.checkbox(

    "Eliminar/Unificar elementos duplicados", value=False

)



sel_archivos = st.sidebar.multiselect(

    "Modelos IFC Auditados:", archivos_disp, default=archivos_disp

)



st.sidebar.markdown("---")

st.sidebar.markdown("### 📈 Control de Progreso BIM")

umbral_mes_anterior = st.sidebar.number_input(

    "Nº Modelos Entrega Mes Anterior:",

    min_value=1,

    max_value=500,

    value=len(archivos_disp),

    step=1,

    help="Regla de avance: nunca puede haber menos modelos que el mes anterior."

)

if len(sel_archivos) >= umbral_mes_anterior:

    st.sidebar.success(

        f"✅ **Cumple No-Regresión:** {len(sel_archivos)} modelos activos "

        f"(>= {umbral_mes_anterior} del mes anterior)."

    )

else:

    st.sidebar.error(

        f"🚨 **Alerta de Regresión:** {len(sel_archivos)} modelos seleccionados "

        f"(faltan {umbral_mes_anterior - len(sel_archivos)} respecto al mes anterior)."

    )



if not sel_archivos:

    st.warning("Selecciona al menos un modelo IFC en la barra lateral.")

    st.stop()



if len(sel_archivos) == len(archivos_disp):

    mask_arr = np.ones(len(df_original), dtype=bool)

else:

    mask_arr = df_original["Archivo_Origen"].isin(sel_archivos).to_numpy()



if unificar_duplicados:

    dup_arr = df_original[["Archivo_Origen", "GlobalId"]].duplicated(

        keep="first"

    ).to_numpy()

    mask_arr = mask_arr & (~dup_arr)



# Un parámetro solo es evaluable dentro de un IFC si el Parquet contiene al menos
# un valor real de ese parámetro en ese modelo. Si no, queda como “no verificable”
# (posible falta de extracción) y no como si todos sus elementos estuvieran vacíos.
mascaras_parametro_modelo = {}
for parametro in params_auditar:
    archivos_con_dato = [
        arch for arch in sel_archivos
        if parametro in parametros_con_dato_por_archivo_apv.get(arch, set())
    ]
    mascaras_parametro_modelo[parametro] = df_original["Archivo_Origen"].isin(
        archivos_con_dato
    ).to_numpy()

parametros_evaluables_por_archivo = {
    arch: sum(
        1 for parametro in params_auditar
        if parametro in parametros_con_dato_por_archivo_apv.get(arch, set())
    )
    for arch in sel_archivos
}

s_pres_arr = np.zeros(len(df_original), dtype=np.uint16)
s_vac_arr = np.zeros(len(df_original), dtype=np.uint16)
for parametro in params_auditar:
    mascara_aplicable = mascaras_parametro_modelo[parametro]
    mascara_vacia = mascara_vacio_rapida(df_original, parametro)
    s_vac_arr += (mascara_aplicable & mascara_vacia).astype(np.uint16)
    s_pres_arr += (mascara_aplicable & ~mascara_vacia).astype(np.uint16)



df_arch_pres = pd.DataFrame({

    "arch": df_original["Archivo_Origen"].to_numpy()[mask_arr],

    "pres": s_pres_arr[mask_arr]

})

suma_arch = df_arch_pres.groupby("arch")["pres"].sum()

archivos_vacios = suma_arch[suma_arch == 0].index.tolist()



n_fantasmas = int(((s_pres_arr == 0) & mask_arr).sum())

if ocultar_fantasmas and n_fantasmas > 0:

    if (s_pres_arr[mask_arr] > 0).any():

        es_arch_vacio = (

            df_original["Archivo_Origen"].isin(archivos_vacios).to_numpy()

        )

        mask_arr = mask_arr & ((s_pres_arr > 0) | es_arch_vacio)

        st.sidebar.success(

            f"🧹 Se filtraron {n_fantasmas:,} sub-elementos sin Psets APV. "

            f"Auditando {int(mask_arr.sum()):,} elementos reales."

        )



total_el = int(mask_arr.sum())

mask_tiene_vacios = mask_arr & (s_vac_arr > 0)

n_inc_total = int(mask_tiene_vacios.sum())



# Pre-cálculo rápido de peso total para uso transversal

if "Peso_Archivo_MB" in df_original.columns:

    df_pesos_global = (

        df_original.loc[mask_arr, ["Archivo_Origen", "Peso_Archivo_MB"]]

        .drop_duplicates(subset=["Archivo_Origen"]).copy()

    )

    df_pesos_global["Peso_Archivo_MB"] = pd.to_numeric(

        df_pesos_global["Peso_Archivo_MB"], errors="coerce"

    ).fillna(0.0)

    peso_total = float(df_pesos_global["Peso_Archivo_MB"].sum())

else:

    df_pesos_global = pd.DataFrame(columns=["Archivo_Origen", "Peso_Archivo_MB"])

    peso_total = 0.0



# --- 17 PESTAÑAS: se conservan las 14 originales y se añaden 3 módulos de control ---

(
    tab1, tab2, tab3, tab4, tab5, tab6, tab7,
    tab8, tab9, tab10, tab11, tab12, tab13, tab14,
    tab15, tab16, tab17
) = st.tabs([
    "📖 1. Cumplimiento BEP Naming",
    "🌍 2. Georreferenciación",
    "🧱 3. Integridad IFC",
    "✍️ 4. Calidad de Formato",
    "🕳️ 5. Auditoría de Vacíos",
    "🎯 6. Navisworks Manage",
    "❤️ 7. Salud del Proyecto",
    "🚨 8. Alertas IFCs Vacíos",
    "📐 9. Grupos de parámetros",
    "🔍 10. Ficha por Elemento",
    "💬 11. Asistente IA",
    "📄 12. Resumen Ejecutivo & PDF",
    "📈 13. Control Avance Mensual",
    "🏗️ 14. Coherencia 4D/5D/6D",
    "🧬 15. Diagnóstico Extracción",
    "🔗 16. Duplicados e IDs",
    "🧭 17. Cobertura por Bloque"
])



# --- PESTAÑA 1 ---

with tab1:

    st.subheader("1. Cumplimiento BEP Naming (Anejo 02) & Sugerencias")

    cols_t1 = [

        c for c in ["Archivo_Origen", "Esquema_IFC", "Peso_Archivo_MB"]

        if c in df_original.columns

    ]

    sub_t1 = df_original[cols_t1].loc[mask_arr]

    conteos_t1 = sub_t1["Archivo_Origen"].value_counts()

    unicos_t1 = sub_t1.drop_duplicates(subset=["Archivo_Origen"])



    res_naming = []

    for _, row in unicos_t1.iterrows():

        arch = row["Archivo_Origen"]

        esquema = row.get("Esquema_IFC", "No definido")

        peso_raw = pd.to_numeric(row.get("Peso_Archivo_MB", 0.0), errors="coerce")

        peso = 0.0 if pd.isna(peso_raw) else float(peso_raw)

        es_ifc_ok = (

            "IFC4" in str(esquema).upper()

            or "IFC2X3" in str(esquema).upper()

        )

        diag = diagnosticar_nombre_bep(arch)

        sugerencia = sugerir_nombre_bep(arch) if "❌" in diag else "✅ Nombre Correcto"

        res_naming.append({

            "Archivo IFC": arch,

            "Cumple Nomenclatura BEP (y Razón Exacta)": diag,

            "Sugerencia de Nombre (BEP APV)": sugerencia,

            "Esquema IFC": esquema,

            "Estado Esquema": "✅ IFC4 / IFC2x3" if es_ifc_ok else "⚠️ Revisar",

            "Peso Extraído (MB)": round(peso, 2),

            "Elementos Reales Auditados": int(conteos_t1.get(arch, 0))

        })

    df_naming_t1 = pd.DataFrame(res_naming)

    st.dataframe(df_naming_t1, width="stretch")



# --- PESTAÑA 2 ---

with tab2:

    st.subheader("2. Auditoría de Georreferenciación (ETRS89 / IfcSite)")

    cols_t2 = [

        c for c in [

            "Archivo_Origen", "EPSG", "Origen_X", "Origen_Y", "Origen_Z",

            "Elevacion_Site", "Latitud_Site", "Longitud_Site"

        ] if c in df_original.columns

    ]

    unicos_t2 = (

        df_original[cols_t2].loc[mask_arr]

        .drop_duplicates(subset=["Archivo_Origen"])

    )

    res_geo = []

    for _, row in unicos_t2.iterrows():

        res_geo.append({

            "Archivo IFC": row["Archivo_Origen"],

            "CRS / EPSG": row.get("EPSG", "No definido"),

            "Origen Site X": row.get("Origen_X", 0.0),

            "Origen Site Y": row.get("Origen_Y", 0.0),

            "Origen Site Z": row.get("Origen_Z", 0.0),

            "Elevación Ref (m)": row.get("Elevacion_Site", 0.0),

            "Latitud (IfcSite)": row.get("Latitud_Site", "No definida"),

            "Longitud (IfcSite)": row.get("Longitud_Site", "No definida")

        })

    df_geo = pd.DataFrame(res_geo)

    st.dataframe(df_geo, width="stretch")

    if len(df_geo) > 1 and (

        df_geo["Origen Site X"].nunique() > 1

        or df_geo["Origen Site Y"].nunique() > 1

    ):

        st.warning(

            "⚠️ Se detectan diferencias en las coordenadas de origen "

            "(IfcSite) entre los distintos modelos."

        )

    else:

        st.success(

            "✅ Consistencia espacial verificada en el emplazamiento (IfcSite)."

        )



# --- PESTAÑA 3 (OPTIMIZADA: SIN TOPE DE 500 Y CON BUSCADOR REAL EN SERVIDOR) ---

with tab3:

    st.subheader("3. Integridad IFC y Clasificación de Entidades")

    sub_t3 = df_original[["Archivo_Origen", "Clase_IFC"]].loc[mask_arr]

    conteo_clases = (

        sub_t3.groupby(["Archivo_Origen", "Clase_IFC"])

        .size()

        .reset_index(name="Cantidad")

    )

    fig_clases = px.bar(

        conteo_clases,

        x="Clase_IFC",

        y="Cantidad",

        color="Archivo_Origen",

        barmode="group",

        title="Distribución de Clases IFC por Modelo"

    )

    st.plotly_chart(fig_clases, width="stretch")



    mask_proxy = mask_arr & (

        df_original["Clase_IFC"].to_numpy() == "IfcBuildingElementProxy"

    )

    n_proxys = int(mask_proxy.sum())

    st.metric("Elementos Genéricos Totales (IfcBuildingElementProxy)", f"{n_proxys:,}")



    st.markdown("---")

    st.markdown("#### 🔎 Buscador e Inspector de Entidades IFC / Proxies (Sobre el 100% de Elementos)")

    col_t3_1, col_t3_2, col_t3_3, col_t3_4 = st.columns([2, 2, 2, 1])



    with col_t3_1:

        mod_t3 = st.multiselect(

            "Filtrar por Modelo IFC:",

            options=sel_archivos,

            default=sel_archivos,

            key="t3_mod_sel"

        )

    with col_t3_2:

        clases_disp_t3 = sorted(sub_t3["Clase_IFC"].dropna().unique().tolist())

        default_clases_t3 = ["IfcBuildingElementProxy"] if "IfcBuildingElementProxy" in clases_disp_t3 else clases_disp_t3

        clase_t3 = st.multiselect(

            "Filtrar por Clase IFC:",

            options=clases_disp_t3,

            default=default_clases_t3,

            key="t3_clase_sel"

        )

    with col_t3_3:

        buscar_t3 = st.text_input(

            "Buscar texto (Nombre, GlobalId, ID_Elemento):",

            placeholder="Ej: cogen, Standard, 2Pz5, #168987...",

            key="t3_search_txt"

        )

    with col_t3_4:

        limite_t3 = st.selectbox(

            "Filas a mostrar:",

            options=[1000, 5000, 15000, 50000, "Todas"],

            index=1,

            key="t3_lim_sel"

        )



    mask_filtro_t3 = (

        mask_arr

        & df_original["Archivo_Origen"].isin(mod_t3).to_numpy()

        & df_original["Clase_IFC"].isin(clase_t3).to_numpy()

    )



    if buscar_t3.strip():

        q_t3 = buscar_t3.strip()

        m_txt_t3 = (

            df_original["GlobalId"].astype(str).str.contains(q_t3, case=False, na=False).to_numpy()

            | df_original[col_id_nativo].astype(str).str.contains(q_t3, case=False, na=False).to_numpy()

        )

        if "Nombre" in df_original.columns:

            m_txt_t3 = m_txt_t3 | df_original["Nombre"].astype(str).str.contains(q_t3, case=False, na=False).to_numpy()

        if "01_09_APV_NOMBRE" in df_original.columns:

            m_txt_t3 = m_txt_t3 | df_original["01_09_APV_NOMBRE"].astype(str).str.contains(q_t3, case=False, na=False).to_numpy()

        mask_filtro_t3 = mask_filtro_t3 & m_txt_t3



    idx_t3_all = np.flatnonzero(mask_filtro_t3)

    n_t3_match = len(idx_t3_all)



    if n_t3_match > 0:

        idx_t3_show = idx_t3_all if limite_t3 == "Todas" else idx_t3_all[:int(limite_t3)]

        cols_p = [

            c for c in [

                "Archivo_Origen", col_id_nativo, "GlobalId", "Clase_IFC", "Nombre", "01_09_APV_NOMBRE"

            ] if c in df_original.columns

        ]

        df_t3_view = df_original[cols_p].iloc[idx_t3_show]

        st.info(f"Mostrando **{len(df_t3_view):,}** de **{n_t3_match:,}** elementos que coinciden con tu filtro.")

        st.dataframe(df_t3_view, width="stretch", height=450)



        csv_t3 = df_original[cols_p].iloc[idx_t3_all].to_csv(index=False).encode("utf-8")

        st.download_button(

            label=f"⬇️ Descargar los {n_t3_match:,} Elementos Filtrados (CSV)",

            data=csv_t3,

            file_name="Auditoria_APV_Integridad_IFC.csv",

            mime="text/csv",

            key="dl_t3_csv"

        )

    else:

        st.success("✅ No se encontraron elementos con esos criterios en la Pestaña 3.")



# --- PESTAÑA 4 (VECTORIZADA Y SIN LÍMITE DE 1,000 REGISTROS) ---

with tab4:

    st.subheader("4. Calidad de Formato (Estricto APV vs BEP) & Buscador por Modelo")

    st.markdown(

        "El comodín **`-`** está permitido por el BEP y no genera error. "

        "Se audita el **100% de los elementos** (unidades, estados de obra, espacios en blanco y textos inválidos)."

    )



    @st.cache_data(show_spinner="Auditando formato en todos los elementos del proyecto...")

    def obtener_errores_formato_vectorizado(
        _df_ref, params_audit, _mask_f, col_id_nat, cache_version_key, _param_masks
    ):

        uni_validas = {"ud", "m", "m2", "dm3", "m3", "kg", "tn", "pa"}

        est_validos = {"Existente", "Demolido", "Temporal", "Proyectado", "Construido"}

        placeholders_malos = {"n/a", "na", "null", "none", "tbd", "sin definir", "por definir", "--", "."}



        lista_dfs = []

        for col in params_audit:

            if col not in _df_ref.columns:
                continue
            mascara_parametro = _param_masks.get(col)
            if mascara_parametro is None or not mascara_parametro.any():
                continue
            s_col = _df_ref[col]

            uniq = s_col.dropna().unique()

            if len(uniq) == 0:

                continue



            es_tmed = "TIPO-MED" in col.upper()

            es_est = "ESTADO" in col.upper()

            mapa_err = {}



            for x in uniq:

                v = str(x)

                v_limpio = v.strip()

                v_low = v_limpio.lower()

                if v_low in VALORES_VACIOS_LOWER or v_limpio == "-":

                    continue

                mot = []

                if v != v_limpio:

                    mot.append("Espacios en blanco al inicio o final")

                if v_low in placeholders_malos:

                    mot.append("Comodín no permitido (debe usarse '-')")

                if es_tmed and v_low not in uni_validas:

                    mot.append(f"Unidad no permitida ('{v_limpio}')")

                elif es_est and v_limpio.capitalize() not in est_validos:

                    mot.append(f"Estado de obra no válido ('{v_limpio}')")

                if mot:

                    mapa_err[x] = " + ".join(mot)



            if mapa_err:

                m_err = (
                    _mask_f
                    & mascara_parametro
                    & s_col.isin(list(mapa_err.keys())).to_numpy()
                )

                if m_err.any():

                    idx_err = np.flatnonzero(m_err)

                    cols_base = ["Archivo_Origen", col_id_nat, "GlobalId", col]

                    if "Clase_IFC" in _df_ref.columns:

                        cols_base.append("Clase_IFC")

                    sub_e = _df_ref[cols_base].iloc[idx_err].copy()

                    sub_e["Parámetro"] = col

                    sub_e["Infracción BEP"] = sub_e[col].map(mapa_err).fillna("Formato")

                    sub_e.rename(columns={

                        "Archivo_Origen": "Archivo",

                        col_id_nat: "ID_Elemento",

                        col: "Contenido Detectado"

                    }, inplace=True)

                    sub_e["Contenido Detectado"] = sub_e["Contenido Detectado"].astype(str)

                    cols_orden = ["Archivo", "ID_Elemento", "GlobalId", "Parámetro", "Contenido Detectado", "Infracción BEP"]

                    if "Clase_IFC" in sub_e.columns:

                        cols_orden.insert(3, "Clase_IFC")

                    lista_dfs.append(sub_e[cols_orden])



        if lista_dfs:

            return pd.concat(lista_dfs, ignore_index=True)

        return pd.DataFrame()



    # Streamlit omite del hash los argumentos cuyo nombre empieza por "_".
    # La clave explícita evita reutilizar errores de formato de otro modelo/filtro.
    cache_version_key = (
        f"{_parquet_stat.st_size}:{_parquet_stat.st_mtime_ns}:"
        f"geo={int(incluir_geo)}:duplicados={int(unificar_duplicados)}:"
        f"fantasmas={int(ocultar_fantasmas)}:"
        f"modelos={'|'.join(sorted(map(str, sel_archivos)))}"
    )
    df_err_fmt_total = obtener_errores_formato_vectorizado(
        df_original, params_auditar, mask_arr, col_id_nativo,
        cache_version_key, mascaras_parametro_modelo
    )


    if not df_err_fmt_total.empty:

        st.error(

            f"⚠️ Se detectaron **{len(df_err_fmt_total):,}** infracciones de formato en total "

            f"en **{df_err_fmt_total['GlobalId'].nunique():,}** elementos únicos."

        )



        c_f4_1, c_f4_2, c_f4_3, c_f4_4 = st.columns([2, 2, 2, 1])

        with c_f4_1:

            arch_err_disp = sorted(df_err_fmt_total["Archivo"].unique().tolist())

            sel_arch_f4 = st.multiselect("Filtrar por Modelo IFC:", arch_err_disp, default=arch_err_disp, key="f4_mod")

        with c_f4_2:

            param_err_disp = sorted(df_err_fmt_total["Parámetro"].unique().tolist())

            sel_param_f4 = st.multiselect("Filtrar por Parámetro:", param_err_disp, default=param_err_disp, key="f4_par")

        with c_f4_3:

            txt_f4 = st.text_input(

                "Buscar ID, GlobalId o Valor erróneo:",

                placeholder="Ej: 3H0K, #168987, m3...",

                key="f4_txt"

            )

        with c_f4_4:

            lim_f4 = st.selectbox(

                "Mostrar filas:",

                options=[1000, 5000, 20000, "Todas"],

                index=1,

                key="f4_lim"

            )



        mask_f4 = (

            df_err_fmt_total["Archivo"].isin(sel_arch_f4)

            & df_err_fmt_total["Parámetro"].isin(sel_param_f4)

        )

        if txt_f4.strip():

            q_f4 = txt_f4.strip()

            mask_f4 = mask_f4 & (

                df_err_fmt_total["ID_Elemento"].astype(str).str.contains(q_f4, case=False, na=False)

                | df_err_fmt_total["GlobalId"].astype(str).str.contains(q_f4, case=False, na=False)

                | df_err_fmt_total["Contenido Detectado"].astype(str).str.contains(q_f4, case=False, na=False)

                | df_err_fmt_total["Infracción BEP"].astype(str).str.contains(q_f4, case=False, na=False)

            )



        df_f4_filtrado = df_err_fmt_total.loc[mask_f4]

        df_f4_show = df_f4_filtrado if lim_f4 == "Todas" else df_f4_filtrado.iloc[:int(lim_f4)]



        st.info(f"Mostrando **{len(df_f4_show):,}** de **{len(df_f4_filtrado):,}** infracciones filtradas.")

        st.dataframe(df_f4_show, width="stretch", height=480)



        csv_f4 = df_f4_filtrado.to_csv(index=False).encode("utf-8")

        st.download_button(

            label=f"⬇️ Descargar las {len(df_f4_filtrado):,} Infracciones de Formato Filtradas (CSV)",

            data=csv_f4,

            file_name="Auditoria_APV_Errores_Formato.csv",

            mime="text/csv",

            key="dl_f4_btn"

        )

    elif not params_auditar:
        st.warning(
            "No se pudo auditar el formato porque no se localizó ningún parámetro oficial "
            "en el Parquet para este filtro. Revisa el diagnóstico de lectura APV que aparece arriba."
        )
    else:
        st.success("✅ Todos los parámetros rellenos cumplen con el formato del BEP.")



# --- PESTAÑA 5 (SOLUCIÓN TOTAL AL BUSCADOR SOBRE LOS 235,360 ELEMENTOS) ---

with tab5:

    st.subheader(

        f"5. Auditoría de los {len(params_auditar)} parámetros APV localizados "
        f"(de {len(PARAMETROS_APV) if incluir_geo else len(PARAMS_NO_GEO)} oficiales aplicables)"

    )

    st.markdown(

        "Si un parámetro contiene **`-`**, se valida como **Comodín BEP "

        "en Verde (`🟢`)**. Si faltan elementos (`🔴`), abajo dispones del **Buscador Global en Servidor** "

        "para filtrar por modelo, por parámetro faltante o buscar cualquier texto sobre el 100% de los elementos."

    )



    cols_ids_ref = df_original[[col_id_nativo, "GlobalId"]]

    resumen_params = []



    for p in params_auditar:
        mask_evaluables = mask_arr & mascaras_parametro_modelo[p]
        n_evaluados = int(mask_evaluables.sum())
        es_vac = mask_evaluables & mascara_vacio_rapida(df_original, p)
        es_com = mask_evaluables & mascara_comodin_rapida(df_original, p)
        n_vac = int(es_vac.sum())
        n_com = int(es_com.sum())
        n_datos = max(0, n_evaluados - n_vac - n_com)
        pct_valido = (
            round(((n_datos + n_com) / n_evaluados) * 100, 1)
            if n_evaluados > 0 else np.nan
        )

        if n_evaluados == 0:
            estado_str = "⚪ No verificable en los modelos seleccionados"
            ids_faltantes, guids_faltantes = "-", "-"
        elif n_vac == 0 and n_com > 0:
            estado_str = "🟢 Comodín BEP (-)"
            ids_faltantes, guids_faltantes = "-", "-"
        elif n_vac == 0:
            estado_str = "🟢 Completo (Dato)"
            ids_faltantes, guids_faltantes = "-", "-"
        else:
            estado_str = f"🔴 Faltan {n_vac:,} elementos"
            idx_f = np.flatnonzero(es_vac)[:30]
            sub_f = cols_ids_ref.iloc[idx_f]
            sufijo = " ..." if n_vac > 30 else ""
            ids_faltantes = ", ".join(sub_f[col_id_nativo].astype(str)) + sufijo
            guids_faltantes = ", ".join(sub_f["GlobalId"].astype(str)) + sufijo

        resumen_params.append({
            "Parámetro Oficial APV": p,
            "Estado Auditoría": estado_str,
            "Elementos Evaluados": n_evaluados,
            "Con Dato Real": n_datos,
            "Con Comodín (-) Válido": n_com,
            "Vacíos (Error)": n_vac,
            "% Cumplimiento (Dato + '-')": pct_valido,
            "ID_Elemento Faltantes (Revit/C3D)": ids_faltantes,
            "GlobalId Faltantes (NWD/IFC)": guids_faltantes
        })

    df_res_vacios = pd.DataFrame(resumen_params, columns=[
        "Parámetro Oficial APV", "Estado Auditoría", "Elementos Evaluados",
        "Con Dato Real", "Con Comodín (-) Válido", "Vacíos (Error)",
        "% Cumplimiento (Dato + '-')", "ID_Elemento Faltantes (Revit/C3D)",
        "GlobalId Faltantes (NWD/IFC)"
    ])



    def colorear_estado(val):
        if "🟢" in str(val):
            return "background-color: #d4edda; color: #155724; font-weight: bold;"
        if "⚪" in str(val):
            return "background-color: #e2e8f0; color: #334155; font-weight: bold;"
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"



    st.dataframe(

        df_res_vacios.style.map(colorear_estado, subset=["Estado Auditoría"]),

        width="stretch"

    )



    if n_inc_total > 0:

        st.markdown("---")

        st.markdown(

            f"#### 🔍 Buscador Global e Inspector de Elementos con Parámetros Vacíos "

            f"(Total detectados: **{n_inc_total:,}** elementos)"

        )

        st.caption(

            "💡 A diferencia de la lupa interna de la tabla, este buscador filtra directamente sobre los "

            f"**{n_inc_total:,} elementos** en memoria antes de mostrar la tabla."

        )



        c_v5_1, c_v5_2, c_v5_3, c_v5_4 = st.columns([2.2, 2.2, 2.2, 1.2])

        with c_v5_1:

            mod_sel_v5 = st.multiselect(

                "1️⃣ Filtrar por Modelo IFC:",

                options=sel_archivos,

                default=sel_archivos,

                key="v5_mod_filter"

            )

        with c_v5_2:

            params_con_vacios = df_res_vacios.loc[df_res_vacios["Vacíos (Error)"] > 0, "Parámetro Oficial APV"].tolist()

            param_esp_v5 = st.selectbox(

                "2️⃣ Filtrar por Parámetro Vacío específico:",

                options=["TODOS (Cualquier parámetro vacío)"] + params_con_vacios,

                index=0,

                key="v5_param_filter"

            )

        with c_v5_3:

            txt_buscar_v5 = st.text_input(

                "3️⃣ Buscar texto (Nombre, GlobalId, ID_Elemento, Clase):",

                placeholder="Ej: cogen, DmBlq, #168987, 3H0Kjj...",

                key="v5_text_search"

            )

        with c_v5_4:

            tam_pag_v5 = st.selectbox(

                "Filas por página:",

                options=[500, 2000, 5000, 10000],

                index=1,

                key="v5_page_size"

            )



        # Construir máscara sobre los 235,360+ elementos

        mask_v5_search = mask_tiene_vacios & df_original["Archivo_Origen"].isin(mod_sel_v5).to_numpy()



        if param_esp_v5 != "TODOS (Cualquier parámetro vacío)":
            mask_v5_search = (
                mask_v5_search
                & mascaras_parametro_modelo[param_esp_v5]
                & mascara_vacio_rapida(df_original, param_esp_v5)
            )



        if txt_buscar_v5.strip():

            q_v5 = txt_buscar_v5.strip()

            m_txt_v5 = (

                df_original["GlobalId"].astype(str).str.contains(q_v5, case=False, na=False).to_numpy()

                | df_original[col_id_nativo].astype(str).str.contains(q_v5, case=False, na=False).to_numpy()

                | df_original["Clase_IFC"].astype(str).str.contains(q_v5, case=False, na=False).to_numpy()

                | df_original["Archivo_Origen"].astype(str).str.contains(q_v5, case=False, na=False).to_numpy()

            )

            if "Nombre" in df_original.columns:

                m_txt_v5 = m_txt_v5 | df_original["Nombre"].astype(str).str.contains(q_v5, case=False, na=False).to_numpy()

            if "01_09_APV_NOMBRE" in df_original.columns:

                m_txt_v5 = m_txt_v5 | df_original["01_09_APV_NOMBRE"].astype(str).str.contains(q_v5, case=False, na=False).to_numpy()

            mask_v5_search = mask_v5_search & m_txt_v5



        idx_v5_all = np.flatnonzero(mask_v5_search)

        n_v5_encontrados = len(idx_v5_all)



        if n_v5_encontrados > 0:

            total_paginas_v5 = max(1, int(np.ceil(n_v5_encontrados / int(tam_pag_v5))))

            col_pg1, col_pg2 = st.columns([1, 3])

            with col_pg1:

                pag_v5 = st.number_input(

                    f"Página (1 a {total_paginas_v5:,}):",

                    min_value=1,

                    max_value=total_paginas_v5,

                    value=1,

                    step=1,

                    key="v5_page_num"

                )

            inicio_v5 = (pag_v5 - 1) * int(tam_pag_v5)

            fin_v5 = min(n_v5_encontrados, inicio_v5 + int(tam_pag_v5))

            idx_inc = idx_v5_all[inicio_v5:fin_v5]



            with col_pg2:

                st.info(

                    f"✅ Se encontraron **{n_v5_encontrados:,}** elementos que coinciden con tu búsqueda. "

                    f"Mostrando filas **{inicio_v5 + 1:,}** a **{fin_v5:,}**."

                )



            cols_b = [

                c for c in [

                    "Archivo_Origen", col_id_nativo, "GlobalId", "Clase_IFC", "Nombre", "01_09_APV_NOMBRE"

                ] if c in df_original.columns

            ]

            df_inc_view = df_original[cols_b].iloc[idx_inc].copy()

            df_inc_view["Cant_Vacios"] = s_vac_arr[idx_inc]



            params_disp = [p for p in params_auditar if p in df_original.columns]

            sub_p = df_original[params_disp].iloc[idx_inc]

            mat_vac = pd.DataFrame(
                {
                    p: mascara_vacio_serie(sub_p[p]) & mascaras_parametro_modelo[p][idx_inc]
                    for p in params_disp
                },
                index=sub_p.index
            )
            df_inc_view["Parámetros_Vacíos"] = mat_vac.apply(
                lambda r: ", ".join(r.index[r.to_numpy(dtype=bool)]), axis=1
            )

            st.dataframe(df_inc_view, width="stretch", height=500)



            col_dl1, col_dl2 = st.columns(2)

            with col_dl1:

                csv_pag_v5 = df_inc_view.to_csv(index=False).encode("utf-8")

                st.download_button(

                    label=f"⬇️ Descargar esta página con detalle de Parámetros Vacíos ({len(df_inc_view):,} filas CSV)",

                    data=csv_pag_v5,

                    file_name=f"Elementos_Vacios_Pagina_{pag_v5}.csv",

                    mime="text/csv",

                    key="dl_v5_pag",

                    width="stretch"

                )

            with col_dl2:

                df_all_v5_export = df_original[cols_b].iloc[idx_v5_all].copy()

                df_all_v5_export["Cant_Vacios"] = s_vac_arr[idx_v5_all]

                csv_all_v5 = df_all_v5_export.to_csv(index=False).encode("utf-8")

                st.download_button(

                    label=f"⬇️ Descargar TODOS los {n_v5_encontrados:,} IDs/GUIDs encontrados (CSV Completo)",

                    data=csv_all_v5,

                    file_name="Auditoria_APV_Todos_Elementos_Vacios_Filtrados.csv",

                    mime="text/csv",

                    key="dl_v5_all",

                    width="stretch"

                )

        else:

            st.warning("⚠️ Ningún elemento con vacíos coincide con ese criterio de búsqueda.")



# --- PESTAÑA 6 ---

with tab6:

    st.subheader(

        "6. Centro de Coordinación e Interferencias para Navisworks Manage"

    )

    c1, c2 = st.columns(2)

    with c1:

        st.markdown("#### 📥 1. Descargar Search Sets XML para Navisworks")

        opciones_nw = (

            ["TODOS los elementos con algún vacío"] + params_auditar

        )

        param_filtro_nw = st.selectbox(

            "Seleccionar grupo de elementos vacíos a aislar:", opciones_nw

        )

        if param_filtro_nw == "TODOS los elementos con algún vacío":

            mask_nw = mask_tiene_vacios

            nombre_xml = "APV_Todos_Los_Vacios"

        else:

            mask_nw = (
                mask_arr
                & mascaras_parametro_modelo[param_filtro_nw]
                & mascara_vacio_rapida(df_original, param_filtro_nw)
            )

            nombre_xml = f"APV_Vacio_{param_filtro_nw}"



        usar_id_nativo = st.checkbox(

            "Usar ID_Elemento nativo (Tag) en lugar de GlobalId", value=True

        )

        n_sel_nw = int(mask_nw.sum())

        st.write(f"Elementos seleccionados para el XML: **{n_sel_nw:,}**")



        if n_sel_nw > 0:

            col_target = col_id_nativo if usar_id_nativo else "GlobalId"

            idx_nw = np.flatnonzero(mask_nw)[:2000]

            vals_nw = (

                df_original[col_target].iloc[idx_nw]

                .dropna().astype(str).unique()

            )

            xml_str = generar_xml_navisworks(

                vals_nw,

                nombre_set=nombre_xml,

                usar_id_nativo=usar_id_nativo

            )

            st.download_button(

                label=f"⬇️ Descargar XML ({min(len(vals_nw), 1000)} elementos)",

                data=xml_str,

                file_name=f"{nombre_xml}.xml",

                mime="text/xml"

            )

        else:

            st.info("No hay elementos vacíos para este filtro seleccionado.")



    with c2:

        st.markdown("#### 🔍 2. Auditoría de IDs Duplicados")

        if total_el > 0:

            sub_d = df_original[["Archivo_Origen", col_id_nativo]].loc[mask_arr]

            m_dup = sub_d.duplicated(

                subset=["Archivo_Origen", col_id_nativo], keep=False

            )

            n_dups = int(m_dup.sum())

            if n_dups > 0:

                st.warning(

                    f"⚠️ Se detectaron **{n_dups:,} elementos** con "

                    "ID_Elemento duplicado (mostrando primeros 500):"

                )

                idx_d = np.flatnonzero(mask_arr)[m_dup.to_numpy()][:500]

                cols_d = [

                    c for c in [

                        "Archivo_Origen", col_id_nativo,

                        "GlobalId", "Clase_IFC", "Nombre"

                    ] if c in df_original.columns

                ]

                st.dataframe(

                    df_original[cols_d].iloc[idx_d],

                    width="stretch"

                )

            else:

                st.success(

                    "✅ No existen ID_Elemento duplicados en los modelos."

                )

        else:

            st.info("Sin datos para analizar duplicados.")



# --- PESTAÑA 7 ---

with tab7:

    st.subheader("7. Salud del Proyecto y Métricas Generales")

    c_s1, c_s2, c_s3 = st.columns(3)

    c_s1.metric("Modelos IFC Analizados", len(sel_archivos))

    c_s2.metric("Total Elementos Auditados", f"{total_el:,}")

    if "Peso_Archivo_MB" in df_original.columns:

        c_s3.metric(

            "Peso Consolidado de Modelos", f"{round(peso_total, 2)} MB"

        )

        fig_peso = px.bar(

            df_pesos_global,

            x="Archivo_Origen",

            y="Peso_Archivo_MB",

            title="Peso de Modelos IFC (MB)",

            text="Peso_Archivo_MB"

        )

        st.plotly_chart(fig_peso, width="stretch")

    else:

        c_s3.metric("Peso Consolidado de Modelos", "0.0 MB")



# --- PESTAÑA 8 ---

with tab8:

    st.subheader("🚨 8. Alertas y Diagnóstico de IFCs Vacíos por Modelo")

    df_t8 = pd.DataFrame({
        "arch": df_original["Archivo_Origen"].to_numpy()[mask_arr],
        "vac": s_vac_arr[mask_arr] > 0
    })

    grp_t8 = df_t8.groupby("arch")["vac"].agg(["count", "sum"])

    resumen_modelos_alt = []

    for arch in sel_archivos:

        tot = int(grp_t8.loc[arch, "count"]) if arch in grp_t8.index else 0

        n_v_m = int(grp_t8.loc[arch, "sum"]) if arch in grp_t8.index else 0

        n_param_modelo = parametros_evaluables_por_archivo.get(arch, 0)

        if n_param_modelo == 0:

            est = "⚪ Sin datos APV verificables en el Parquet"

        elif tot == 0:

            est = "🚨 IFC Vacío"

        elif n_v_m == tot:

            est = "🚨 100% Incompleto"

        elif n_v_m > 0:

            est = f"🔴 Parcial ({n_v_m:,} vacíos)"

        else:

            est = "🟢 100% Completo"

        resumen_modelos_alt.append({

            "Archivo IFC": arch,

            "Elementos": tot,

            "Estado General": est

        })

    st.dataframe(pd.DataFrame(resumen_modelos_alt), width="stretch")



# --- PESTAÑA 9 ---

with tab9:

    st.subheader("📐 Grupos de parámetros")

    st.markdown(

        "Informe detallado por modelo sobre los bloques y grupos de "

        "parámetros detectados según la directriz del BEP "

        "(**Geotecnia = 11 grupos**; **Resto de modelos = 9 grupos**)."

    )

    st.dataframe(df_informe_grupos, width="stretch")



# --- PESTAÑA 10 (DISEÑO DETALLADO CON DESPLEGABLE + COPIAR Y PEGAR GUID / ID) ---

with tab10:

    st.subheader("🔍 10. Ficha Detallada por Elemento (Inspector BIM)")

    st.markdown(

        "Selecciona un elemento de la lista desplegable o **copia y pega directamente su `GlobalId` o `ID_Elemento`** "

        "(por ejemplo, desde las Pestañas 3, 4 o 5) para auditar todos sus parámetros APV al detalle."

    )



    ids_disponibles_t10 = df_original.loc[mask_arr, "GlobalId"].dropna().unique()[:5000]



    col_sel10, col_paste10 = st.columns(2)

    with col_sel10:

        idx_default_10 = 0

        if "3H0KjjMnv619yNSGbFXGIK" in ids_disponibles_t10:

            idx_default_10 = int(np.where(ids_disponibles_t10 == "3H0KjjMnv619yNSGbFXGIK")[0][0])

        id_seleccionado_lista = st.selectbox(

            "Selecciona un GlobalId de la lista:",

            options=ids_disponibles_t10,

            index=idx_default_10,

            key="select_ficha_globalid"

        )

    with col_paste10:

        id_pegado_texto = st.text_input(

            "📋 O copia y pega aquí cualquier GlobalId o ID_Elemento (prioritario):",

            value="",

            placeholder="Pega aquí ej: 3H0KjjMnv619yNSGbFXGIK o #168987 o 152831",

            key="paste_ficha_id"

        )



    # Resolver qué elemento inspeccionar

    elem_df_match = pd.DataFrame()

    criterio_usado = ""

    if id_pegado_texto.strip():

        q10 = id_pegado_texto.strip()

        criterio_usado = q10

        # 1. Intentar coincidencia exacta en GlobalId o ID_Elemento

        m_exact = (

            (df_original["GlobalId"].astype(str) == q10)

            | (df_original[col_id_nativo].astype(str) == q10)

        )

        if m_exact.any():

            elem_df_match = df_original.loc[m_exact]

        else:

            # 2. Intentar coincidencia parcial

            m_part = (

                df_original["GlobalId"].astype(str).str.contains(q10, case=False, na=False)

                | df_original[col_id_nativo].astype(str).str.contains(q10, case=False, na=False)

            )

            elem_df_match = df_original.loc[m_part]

    elif len(ids_disponibles_t10) > 0:

        criterio_usado = str(id_seleccionado_lista)

        elem_df_match = df_original.loc[df_original["GlobalId"] == id_seleccionado_lista]



    if not elem_df_match.empty:

        if len(elem_df_match) > 1:

            st.info(f"🔎 Se encontraron **{len(elem_df_match)}** elementos que coinciden con `{criterio_usado}`. Mostrando el primero (puedes elegir otro abajo):")

            opciones_desempate = [

                f"{r['GlobalId']} | ID: {r[col_id_nativo]} | {r['Archivo_Origen']}"

                for _, r in elem_df_match.head(50).iterrows()

            ]

            eleccion_desempate = st.selectbox("Elegir coincidencia exacta:", opciones_desempate, key="t10_desempate")

            guid_elegido = eleccion_desempate.split(" | ")[0]

            elem_info = elem_df_match.loc[elem_df_match["GlobalId"].astype(str) == guid_elegido].iloc[0]

        else:

            elem_info = elem_df_match.iloc[0]



        guid_actual = elem_info.get("GlobalId", "N/A")

        with st.expander(f"📋 Ficha Detallada del Elemento: {guid_actual}", expanded=True):

            col_f1, col_f2, col_f3 = st.columns(3)

            with col_f1:

                st.metric("Clase IFC", str(elem_info.get("Clase_IFC", "N/A")))

                st.metric("Archivo Origen", str(elem_info.get("Archivo_Origen", "N/A")))

            with col_f2:

                st.metric("ID Nativo (Revit/C3D)", str(elem_info.get(col_id_nativo, "N/A")))

                st.metric("Nombre Objeto", str(elem_info.get("Nombre", elem_info.get("01_09_APV_NOMBRE", "N/A"))))

            with col_f3:

                n_vacios_elem = 0

                n_comodines_elem = 0

                n_datos_elem = 0

                filas_ficha = []
                archivo_ficha = str(elem_info.get("Archivo_Origen", ""))
                params_ficha = [
                    p for p in params_auditar
                    if p in parametros_con_dato_por_archivo_apv.get(archivo_ficha, set())
                ]

                for p in params_ficha:

                    val_p = elem_info.get(p, np.nan)

                    es_v = es_valor_vacio(val_p)

                    es_c = (not es_v) and str(val_p).replace("\u00a0", " ").strip() == "-"

                    if es_v:

                        n_vacios_elem += 1

                        est_p = "🔴 Vacío (Falta Dato)"

                    elif es_c:

                        n_comodines_elem += 1

                        est_p = "🟡 Comodín BEP (-)"

                    else:

                        n_datos_elem += 1

                        est_p = "🟢 Relleno (OK)"

                    filas_ficha.append({

                        "Grupo BEP": p.split("_")[0],

                        "Parámetro BEP": p,

                        "Valor Actual": "" if pd.isna(val_p) else str(val_p),

                        "Estado": est_p

                    })

                pct_obj = round(((n_datos_elem + n_comodines_elem) / max(1, len(params_ficha))) * 100, 1) if params_ficha else 0.0

                st.metric("Parámetros APV Vacíos", n_vacios_elem, delta=f"{pct_obj}% Cumplimiento", delta_color="inverse")

                st.caption(
                    f"🟢 Con dato: **{n_datos_elem}** | 🟡 Comodín (-): **{n_comodines_elem}** | "
                    f"🔴 Vacíos: **{n_vacios_elem}** | ⚪ No verificables en este IFC: **{len(params_auditar) - len(params_ficha)}**"
                )
                if not params_ficha:
                    st.warning("Este IFC no tiene valores APV extraídos verificables en el Parquet. La ficha no lo considera 100 % incompleto: requiere revisar la exportación de origen.")



            st.markdown("##### 📊 Auditoría Individual de Parámetros APV de este Objeto:")

            filtro_vista_ficha = st.radio(

                "Filtrar parámetros de la ficha:",

                options=["Todos los Parámetros", "🔴 Solo Parámetros Vacíos (Que Fallan)", "🟢 Solo Parámetros Rellenos / Comodín"],

                horizontal=True,

                key="t10_radio_filtro"

            )

            df_ficha = pd.DataFrame(filas_ficha)

            if "🔴" in filtro_vista_ficha:

                df_ficha = df_ficha[df_ficha["Estado"].str.contains("🔴")]

            elif "🟢" in filtro_vista_ficha:

                df_ficha = df_ficha[~df_ficha["Estado"].str.contains("🔴")]



            def estilo_fila_ficha(val):

                if "🔴" in str(val):

                    return "background-color: #f8d7da; color: #721c24; font-weight: bold;"

                if "🟡" in str(val):

                    return "background-color: #fff3cd; color: #856404; font-weight: bold;"

                return "background-color: #d4edda; color: #155724; font-weight: bold;"



            st.dataframe(

                df_ficha.style.map(estilo_fila_ficha, subset=["Estado"]),

                width="stretch",

                hide_index=True,

                height=450

            )

    else:

        st.error(f"❌ No se encontró ningún elemento con el identificador `{criterio_usado}` en la base de datos.")



# --- PESTAÑA 11 (ASISTENTE IA CONVERSACIONAL CONECTADO A TUS DATOS REALES) ---

with tab11:

    st.subheader("💬 11. Asistente IA de Entrega y Auditoría BIM - APV")

    st.markdown(

        "Haz preguntas en lenguaje natural sobre tu entrega: **qué modelos tienen más errores, qué parámetros faltan, "

        "estado de un archivo `.ifc` específico, proxies, pesos o reglas del BEP**."

    )
    st.caption(
        "El asistente actual responde usando reglas y métricas calculadas desde esta auditoría; "
        "no llama todavía a un modelo generativo externo ni requiere una API key."
    )



    if "messages" not in st.session_state:

        st.session_state.messages = [

            {

                "role": "assistant",

                "content": (

                    f"¡Hola Claudia! Estoy conectado en vivo a los **{len(sel_archivos)} modelos IFC** "

                    f"(**{total_el:,} elementos**). Puedes preguntarme cosas como:\n"

                    "- *¿Cuáles son los 5 parámetros que más fallan?*\n"

                    "- *¿Qué modelos tienen peor cumplimiento BEP?*\n"

                    "- *¿Cuántos proxies hay y en qué modelos están?*\n"

                    "- *¿Cumplimos la regla de avance respecto al mes anterior?*"

                )

            }

        ]



    for message in st.session_state.messages:

        with st.chat_message(message["role"]):

            st.markdown(message["content"])



    if prompt := st.chat_input("Escribe tu consulta sobre la entrega BIM de la APV..."):

        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.chat_message("user"):

            st.markdown(prompt)



        with st.chat_message("assistant"):

            p_low = prompt.lower()

            top_vacios_ia = (
                df_res_vacios.loc[df_res_vacios["Elementos Evaluados"] > 0]
                .sort_values("Vacíos (Error)", ascending=False).head(5)
            )



            if any(k in p_low for k in ["parametro", "parámetro", "fallan", "peor", "critico", "crítico"]):
                if top_vacios_ia.empty:
                    respuesta = (
                        "No hay parámetros con celdas verificables para generar un ranking fiable. "
                        "Revisa el diagnóstico de lectura APV del inicio del dashboard y la exportación Parquet."
                    )
                else:
                    lineas_p = "\n".join([
                        f"- **`{r['Parámetro Oficial APV']}`**: faltan **{r['Vacíos (Error)']:,}** elementos "
                        f"({r[COL_PCT_CUMPLIMIENTO]}% cumplido sobre {r['Elementos Evaluados']:,} elementos evaluados)."
                        for _, r in top_vacios_ia.iterrows()
                    ])
                    respuesta = (
                        f"Los **5 parámetros oficiales APV con más vacíos verificables** en esta entrega son:\n\n{lineas_p}\n\n"
                        "💡 *Puedes ir a la **Pestaña 5** y seleccionar cualquiera de ellos en el desplegable `2️⃣ Filtrar por Parámetro Vacío` para ver exactamente qué elementos son.*"
                    )

            elif any(k in p_low for k in ["proxy", "proxies", "generico", "genérico"]):

                respuesta = (

                    f"Actualmente se detectan **{n_proxys:,} elementos `IfcBuildingElementProxy`** en los modelos seleccionados. "

                    "En la **Pestaña 3** tienes el buscador desbloqueado para filtrarlos por modelo y descargar el listado completo en CSV."

                )

            elif any(k in p_low for k in ["formato", "unidad", "estado"]):

                respuesta = (

                    f"En la auditoría estricta de formato (**Pestaña 4**) se han detectado **{len(df_err_fmt_total):,} infracciones** "

                    f"repartidas en **{df_err_fmt_total['Archivo'].nunique() if not df_err_fmt_total.empty else 0} modelos IFC**."

                )

            elif any(k in p_low for k in ["mes", "anterior", "avance", "regresion", "regresión"]):

                estado_reg = "✅ CUMPLE" if len(sel_archivos) >= umbral_mes_anterior else "🚨 INCUMPLE"

                respuesta = (

                    f"Respecto al control de avance mensual: tienes **{len(sel_archivos)} modelos activos** frente al umbral de "

                    f"**{umbral_mes_anterior} modelos** del mes anterior (**{estado_reg}** la regla de no-regresión)."

                )

            else:

                pct_global_ia = round(float(df_res_vacios["% Cumplimiento (Dato + '-')"].mean()), 1) if not df_res_vacios.empty else 0.0

                respuesta = (

                    f"**Resumen en vivo de tu entrega APV:**\n"

                    f"- **Modelos IFC auditados:** {len(sel_archivos)} archivos ({round(peso_total, 2)} MB)\n"

                    f"- **Elementos reales auditados:** {total_el:,} objetos\n"

                    f"- **Cumplimiento medio de parámetros BEP:** {pct_global_ia}%\n"

                    f"- **Elementos con al menos un vacío:** {n_inc_total:,}\n"

                    f"- **Infracciones de formato:** {len(df_err_fmt_total):,}\n\n"

                    "Pregúntame por *parámetros críticos*, *proxies*, *errores de formato* o revisa la **Pestaña 12** para descargar el informe ejecutivo con hipervínculos."

                )



            st.markdown(respuesta)

            st.session_state.messages.append({"role": "assistant", "content": respuesta})



# --- PESTAÑA 12 (RESUMEN EJECUTIVO VISUAL DE ALTO IMPACTO & DESCARGA CON HIPERVÍNCULOS) ---

with tab12:

    fecha_actual_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    st.subheader("📄 12. Resumen Ejecutivo de Dirección & Exportación Interactiva - APV")

    st.caption(f"Autoridad Portuaria de Valencia (APV) · Contrato N035 · Fecha de emisión: {fecha_actual_str}")



    # Cálculos ejecutivos consolidados

    total_celdas_verificables = int(df_res_vacios["Elementos Evaluados"].sum())
    total_celdas_auditadas = max(1, total_celdas_verificables)

    total_celdas_datos = int(df_res_vacios["Con Dato Real"].sum())

    total_celdas_comodin = int(df_res_vacios["Con Comodín (-) Válido"].sum())

    total_celdas_vacias = int(df_res_vacios["Vacíos (Error)"].sum())

    pct_cumplimiento_global = (
        round(((total_celdas_datos + total_celdas_comodin) / total_celdas_auditadas) * 100, 1)
        if total_celdas_verificables > 0 else 0.0
    )



    n_naming_ok = sum(1 for r in res_naming if "✅" in r["Cumple Nomenclatura BEP (y Razón Exacta)"])

    pct_naming_ok = round((n_naming_ok / max(1, len(res_naming))) * 100, 1)



    geo_consistente = not (

        len(df_geo) > 1 and (df_geo["Origen Site X"].nunique() > 1 or df_geo["Origen Site Y"].nunique() > 1)

    )



    # 1. Tarjetas KPI de Dirección (6 indicadores clave)

    k1, k2, k3, k4, k5, k6 = st.columns(6)

    with k1:

        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Modelos IFC</div><div class="kpi-value">{len(sel_archivos)}</div><div class="kpi-sub">Umbral mes ant: {umbral_mes_anterior}</div></div>', unsafe_allow_html=True)

    with k2:

        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Elementos BIM</div><div class="kpi-value">{total_el:,}</div><div class="kpi-sub">Auditados reales</div></div>', unsafe_allow_html=True)

    with k3:

        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Cumplimiento BEP</div><div class="kpi-value">{pct_cumplimiento_global}%</div><div class="kpi-sub">Dato + Comodín (-)</div></div>', unsafe_allow_html=True)

    with k4:

        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Naming Anejo 02</div><div class="kpi-value">{pct_naming_ok}%</div><div class="kpi-sub">{n_naming_ok}/{len(res_naming)} Modelos OK</div></div>', unsafe_allow_html=True)

    with k5:

        est_geo_kpi = "100% OK" if geo_consistente else "ALERTA"

        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Georreferenciación</div><div class="kpi-value">{est_geo_kpi}</div><div class="kpi-sub">ETRS89 / IfcSite</div></div>', unsafe_allow_html=True)

    with k6:

        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Peso Consolidado</div><div class="kpi-value">{round(peso_total, 1)} MB</div><div class="kpi-sub">{n_proxys:,} Proxies</div></div>', unsafe_allow_html=True)



    st.markdown("<br>", unsafe_allow_html=True)

    modelos_sin_datos_verificables = [
        arch for arch in sel_archivos
        if parametros_evaluables_por_archivo.get(arch, 0) == 0
    ]
    if modelos_sin_datos_verificables:
        st.warning(
            "No se puede emitir un dictamen de cumplimiento de parámetros APV para "
            f"{len(modelos_sin_datos_verificables)} modelo(s), porque el Parquet no contiene "
            "ningún valor APV verificable para ellos: "
            + ", ".join(modelos_sin_datos_verificables)
            + ". Se muestran como 'No verificable', no como 100 % incompletos ni como completos. "
            "El porcentaje global solo considera celdas evaluables."
        )

    # Construcción de Matriz de Calidad por Modelo IFC

    df_mod_stats = pd.DataFrame({

        "Archivo_Origen": df_original["Archivo_Origen"].to_numpy()[mask_arr],

        "vac_count": s_vac_arr[mask_arr],

        "params_evaluables": df_original["Archivo_Origen"].map(parametros_evaluables_por_archivo).fillna(0).to_numpy()[mask_arr],

        "es_proxy": (df_original["Clase_IFC"].to_numpy()[mask_arr] == "IfcBuildingElementProxy")

    })

    grp_mod_exec = df_mod_stats.groupby("Archivo_Origen").agg(

        Elementos=("vac_count", "count"),

        Elem_Con_Vacios=("vac_count", lambda x: int((x > 0).sum())),

        Suma_Celdas_Vacias=("vac_count", "sum"),

        Parámetros_Evaluables=("params_evaluables", "first"),

        Proxies=("es_proxy", "sum")

    ).reset_index()



    grp_mod_exec["Total_Celdas_Modelo"] = grp_mod_exec["Elementos"] * grp_mod_exec["Parámetros_Evaluables"]

    grp_mod_exec["Celdas_Cumplidas"] = grp_mod_exec["Total_Celdas_Modelo"] - grp_mod_exec["Suma_Celdas_Vacias"]

    grp_mod_exec["% Cumplimiento BEP"] = (
        (grp_mod_exec["Celdas_Cumplidas"] / grp_mod_exec["Total_Celdas_Modelo"].replace(0, np.nan)) * 100
    ).round(1)

    grp_mod_exec["% Vacíos"] = (100.0 - grp_mod_exec["% Cumplimiento BEP"]).round(1)

    grp_mod_exec["Naming BEP"] = grp_mod_exec["Archivo_Origen"].apply(

        lambda a: "✅ OK" if "✅" in diagnosticar_nombre_bep(a) else "❌ Error"

    )



    def dictamen_modelo(row):
        if pd.isna(row["% Cumplimiento BEP"]):
            return "⚪ NO VERIFICABLE (sin datos APV extraídos)"
        if row["% Cumplimiento BEP"] >= 95 and row["Naming BEP"] == "✅ OK":

            return "🟢 APTO"

        if row["% Cumplimiento BEP"] >= 75:

            return "🟡 CON OBSERVACIONES"

        return "🔴 REQUIERE CORRECCIÓN"



    grp_mod_exec["Dictamen Técnico"] = grp_mod_exec.apply(dictamen_modelo, axis=1)



    # 2. Primera fila de gráficos ejecutivos: Donut Global + Ranking de Cumplimiento por Modelo

    col_g1, col_g2 = st.columns([1.1, 1.9])

    with col_g1:

        df_donut = pd.DataFrame({

            "Estado de Celdas BEP": ["Con Dato Real", "Comodín BEP (-)", "Vacíos (Incumplimiento)"],

            "Cantidad": [total_celdas_datos, total_celdas_comodin, total_celdas_vacias]

        })

        fig_donut = px.pie(

            df_donut,

            names="Estado de Celdas BEP",

            values="Cantidad",

            hole=0.58,

            color="Estado de Celdas BEP",

            color_discrete_map={

                "Con Dato Real": "#10b981",

                "Comodín BEP (-)": "#3b82f6",

                "Vacíos (Incumplimiento)": "#ef4444"

            },

            title="Balance Global de Celdas Auditadas vs BEP"

        )

        fig_donut.update_traces(textposition="inside", textinfo="percent+label")

        st.plotly_chart(fig_donut, width="stretch")



    with col_g2:

        df_rank_mod = grp_mod_exec.sort_values("% Cumplimiento BEP", ascending=True)

        fig_rank = px.bar(

            df_rank_mod,

            y="Archivo_Origen",

            x=["% Cumplimiento BEP", "% Vacíos"],

            orientation="h",

            title="Índice de Madurez y Cumplimiento BEP por Modelo IFC (%)",

            color_discrete_map={"% Cumplimiento BEP": "#10b981", "% Vacíos": "#ef4444"},

            text_auto=".1f"

        )

        fig_rank.update_layout(barmode="stack", xaxis_title="% de Parámetros Oficiales APV", yaxis_title="Modelo IFC")

        st.plotly_chart(fig_rank, width="stretch")



    # 3. Segunda fila de gráficos ejecutivos: Cumplimiento por Bloques del BEP (01 a 10) + Top 12 Parámetros Críticos

    col_g3, col_g4 = st.columns(2)

    with col_g3:

        df_res_vacios["Codigo_Grupo"] = df_res_vacios["Parámetro Oficial APV"].apply(

            lambda x: x.split("-")[0] if "-" in x.split("_")[0] else x.split("_")[0]

        )

        df_res_vacios["Nombre_Bloque_BEP"] = df_res_vacios["Codigo_Grupo"].map(NOMBRES_GRUPOS_BEP).fillna("Otros")

        grp_bloques = df_res_vacios.groupby("Nombre_Bloque_BEP", as_index=False)["% Cumplimiento (Dato + '-')"].mean()

        grp_bloques["% Cumplimiento Medio"] = grp_bloques["% Cumplimiento (Dato + '-')"].round(1)



        fig_bloques = px.bar(

            grp_bloques.sort_values("% Cumplimiento Medio", ascending=True),

            x="% Cumplimiento Medio",

            y="Nombre_Bloque_BEP",

            orientation="h",

            color="% Cumplimiento Medio",

            color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],

            range_x=[0, 105],

            text="% Cumplimiento Medio",

            title="Cumplimiento Medio por Dimensión / Bloque del BEP APV (%)"

        )

        st.plotly_chart(fig_bloques, width="stretch")



    with col_g4:

        df_top_crit = (
            df_res_vacios.loc[df_res_vacios["Elementos Evaluados"] > 0]
            .sort_values("Vacíos (Error)", ascending=False).head(12)
            .sort_values("Vacíos (Error)", ascending=True)
        )

        fig_pareto = px.bar(

            df_top_crit,

            x="Vacíos (Error)",

            y="Parámetro Oficial APV",

            orientation="h",

            color="Vacíos (Error)",

            color_continuous_scale="Reds",

            text="Vacíos (Error)",

            title="Top 12 Parámetros APV con Mayor Volumen de Incumplimiento"

        )

        st.plotly_chart(fig_pareto, width="stretch")



    # 4. Matriz Ejecutiva de Semáforo por Modelo IFC

    st.markdown("#### 🚦 Matriz Ejecutiva de Calidad por Modelo IFC")

    cols_matriz_exec = [

        "Archivo_Origen", "Dictamen Técnico", "Naming BEP", "Elementos",

        "Parámetros_Evaluables", "Elem_Con_Vacios", "Proxies", "% Cumplimiento BEP"

    ]

    df_matriz_exec_ordenada = grp_mod_exec[cols_matriz_exec].sort_values(
        "% Cumplimiento BEP", ascending=False, na_position="last"
    ).reset_index(drop=True)
    st.dataframe(
        df_matriz_exec_ordenada,
        width="stretch",
        hide_index=True
    )

    # Exportación IFC del resumen: crea registros esquemáticos con propiedades de auditoría.
    st.markdown("#### 🧱 Exportar esta matriz como IFC de auditoría")
    st.caption(
        "El IFC resultante contiene una caja seleccionable por cada modelo de la matriz, con sus métricas "
        "como propiedades IFC. No contiene ni sustituye la geometría original de los modelos auditados. "
        "Está pensado para consultar los dictámenes y propiedades del informe en Navisworks."
    )
    cols_ifc_matriz = [
        c for c in cols_matriz_exec + ["% Vacíos", "Total_Celdas_Modelo", "Celdas_Cumplidas", "Suma_Celdas_Vacias"]
        if c in grp_mod_exec.columns
    ]
    df_ifc_matriz = grp_mod_exec[cols_ifc_matriz].sort_values(
        "% Cumplimiento BEP", ascending=False, na_position="last"
    ).reset_index(drop=True)
    huella_ifc = hashlib.sha256(df_ifc_matriz.to_csv(index=False).encode("utf-8")).hexdigest()
    if st.session_state.get("ifc_matriz_huella") != huella_ifc:
        st.session_state.pop("ifc_matriz_bytes", None)
        st.session_state.pop("ifc_matriz_huella", None)
    if st.button("⚙️ Generar IFC de la Matriz Ejecutiva", key="t12_generar_ifc"):
        try:
            with st.spinner("Generando IFC4 de auditoría con propiedades por modelo..."):
                bytes_ifc = generar_ifc_matriz_auditoria(df_ifc_matriz, fecha_actual_str)
            st.session_state["ifc_matriz_bytes"] = bytes_ifc
            st.session_state["ifc_matriz_huella"] = huella_ifc
            st.success(f"IFC de auditoría generado: {len(df_ifc_matriz)} registros de modelo.")
        except Exception as exc:
            st.error(f"No se pudo generar el IFC de auditoría: {exc}")
    if (
        st.session_state.get("ifc_matriz_huella") == huella_ifc
        and st.session_state.get("ifc_matriz_bytes")
    ):
        st.download_button(
            "⬇️ Descargar Matriz Ejecutiva IFC4",
            data=st.session_state["ifc_matriz_bytes"],
            file_name="Matriz_Ejecutiva_Calidad_Modelos_APV.ifc",
            mime="application/x-step",
            key="t12_descargar_ifc",
            help="IFC4 de informe: cajas esquemáticas con las propiedades de auditoría por modelo."
        )

    st.markdown("---")

    st.markdown("#### 🚀 Centro de Descarga de Informe Ejecutivo con Hipervínculos (PDF / HTML / Excel)")



    # Generador de Informe Ejecutivo Interactivo HTML/PDF con Hipervínculos

    filas_html_modelos = "".join([
        f"<tr><td>{r['Archivo_Origen']}</td><td><b>{r['Dictamen Técnico']}</b></td>"
        f"<td>{r['Naming BEP']}</td><td>{r['Elementos']:,}</td>"
        f"<td>{int(r['Parámetros_Evaluables']):,}</td><td>{r['Elem_Con_Vacios']:,}</td>"
        f"<td>{int(r['Proxies']):,}</td>"
        f"<td><b>{'N/V' if pd.isna(r['% Cumplimiento BEP']) else str(r['% Cumplimiento BEP']) + '%'}</b></td></tr>"
        for _, r in grp_mod_exec.sort_values("% Cumplimiento BEP", ascending=False, na_position="last").iterrows()
    ])

    filas_html_bloques = "".join([
        f"<tr><td>{r['Nombre_Bloque_BEP']}</td><td><b>{r['% Cumplimiento Medio']}%</b></td></tr>"
        for _, r in grp_bloques.sort_values("Nombre_Bloque_BEP").iterrows()
    ])

    filas_html_top_vacios = "".join([
        f"<tr><td>{r['Parámetro Oficial APV']}</td><td>{r['Estado Auditoría']}</td>"
        f"<td>{int(r['Elementos Evaluados']):,}</td><td>{int(r['Con Dato Real']):,}</td>"
        f"<td>{int(r['Con Comodín (-) Válido']):,}</td><td><b>{int(r['Vacíos (Error)']):,}</b></td>"
        f"<td><b>{'N/V' if pd.isna(r[COL_PCT_CUMPLIMIENTO]) else str(r[COL_PCT_CUMPLIMIENTO]) + '%'}</b></td></tr>"
        for _, r in df_res_vacios.loc[df_res_vacios["Elementos Evaluados"] > 0]
            .sort_values("Vacíos (Error)", ascending=False).head(25).iterrows()
    ])


    html_ejecutivo = f"""<!DOCTYPE html>

<html lang="es">

<head>

<meta charset="UTF-8">

<title>Informe Ejecutivo Auditoría BIM - APV</title>

<style>

    body {{ font-family: 'Segoe UI', Roboto, Arial, sans-serif; margin: 32px; color: #1e293b; background: #f8fafc; }}

    .header {{ background: #0f172a; color: white; padding: 24px 32px; border-radius: 12px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }}

    .nav {{ background: #e2e8f0; padding: 12px 20px; border-radius: 8px; margin-bottom: 24px; display: flex; gap: 18px; flex-wrap: wrap; }}

    .nav a {{ color: #0284c7; font-weight: 600; text-decoration: none; }}

    .nav a:hover {{ text-decoration: underline; }}

    .btn-print {{ background: #0284c7; color: white; border: none; padding: 10px 18px; border-radius: 6px; cursor: pointer; font-weight: bold; }}

    .kpis {{ display: grid; grid-template-columns: repeat(6, 1fr); gap: 12px; margin-bottom: 24px; }}

    .kpi {{ background: white; border: 1px solid #cbd5e1; border-radius: 8px; padding: 14px; text-align: center; }}

    .kpi h4 {{ margin: 0; font-size: 12px; color: #64748b; text-transform: uppercase; }}

    .kpi p {{ margin: 6px 0 0 0; font-size: 22px; font-weight: 700; color: #0f172a; }}

    table {{ width: 100%; border-collapse: collapse; background: white; margin-bottom: 28px; font-size: 13px; }}

    th, td {{ border: 1px solid #cbd5e1; padding: 8px 12px; text-align: left; }}

    th {{ background: #0f172a; color: white; }}

    tr:nth-child(even) {{ background: #f1f5f9; }}

    h2 {{ color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 6px; margin-top: 28px; }}

    @media print {{ .no-print {{ display: none !important; }} body {{ background: white; margin: 10px; }} }}

</style>

</head>

<body>

    <div class="header">

        <div>

            <h1 style="margin:0; font-size:24px;">📋 Acta Ejecutiva de Auditoría BIM & Cumplimiento BEP</h1>

            <p style="margin:4px 0 0 0; color:#94a3b8;">Autoridad Portuaria de Valencia (APV) · Contrato N035 · Emitido: {fecha_actual_str}</p>

        </div>

        <button class="btn-print no-print" onclick="window.print()">🖨️ Imprimir / Guardar en PDF</button>

    </div>



    <div class="nav no-print">

        <span><b>🔗 Índice Rápido con Hipervínculos:</b></span>

        <a href="#seccion-kpis">1. KPIs Ejecutivos</a>

        <a href="#seccion-matriz">2. Matriz por Modelo IFC</a>

        <a href="#seccion-bloques">3. Cumplimiento por Bloques BEP</a>

        <a href="#seccion-criticos">4. Top Parámetros Críticos</a>

        <a href="https://ausep2.streamlit.app/" target="_blank">🌐 Abrir Dashboard Interactivo en Vivo (APV)</a>

    </div>



    <h2 id="seccion-kpis">1. Indicadores Clave de Rendimiento (KPIs)</h2>

    <div class="kpis">

        <div class="kpi"><h4>Modelos Auditados</h4><p>{len(sel_archivos)} IFCs</p></div>

        <div class="kpi"><h4>Elementos Reales</h4><p>{total_el:,}</p></div>

        <div class="kpi"><h4>Cumplimiento BEP</h4><p>{pct_cumplimiento_global}%</p></div>

        <div class="kpi"><h4>Naming Anejo 02</h4><p>{pct_naming_ok}%</p></div>

        <div class="kpi"><h4>Georreferenciación</h4><p>{"OK" if geo_consistente else "Revisar"}</p></div>

        <div class="kpi"><h4>Peso Consolidado</h4><p>{round(peso_total, 2)} MB</p></div>

    </div>



    <p><b>Nota de lectura:</b> el cumplimiento global se calcula solo sobre celdas verificables en el Parquet. Los modelos o parámetros sin valores extraídos se marcan como no verificables; no se consideran automáticamente incumplidos ni completos.</p>

    <h2 id="seccion-matriz">2. Matriz Ejecutiva de Calidad por Modelo IFC</h2>

    <table>

        <thead>

            <tr>

                <th>Archivo IFC</th><th>Dictamen Técnico</th><th>Naming BEP</th>

                <th>Elementos Auditados</th><th>Parámetros Evaluables</th><th>Elementos con Vacíos</th><th>Proxies</th><th>% Cumplimiento BEP</th>

            </tr>

        </thead>

        <tbody>{filas_html_modelos}</tbody>

    </table>



    <h2 id="seccion-bloques">3. Cumplimiento por Dimensiones y Bloques del BEP APV</h2>

    <table>

        <thead><tr><th>Bloque / Dimensión del BEP</th><th>% Cumplimiento Medio</th></tr></thead>

        <tbody>{filas_html_bloques}</tbody>

    </table>



    <h2 id="seccion-criticos">4. Top 25 Parámetros Oficiales APV con Mayor Número de Vacíos</h2>

    <table>

        <thead>

            <tr>

                <th>Parámetro Oficial APV</th><th>Estado</th><th>Elementos Evaluados</th><th>Con Dato Real</th>

                <th>Con Comodín (-)</th><th>Vacíos (Error)</th><th>% Cumplimiento</th>

            </tr>

        </thead>

        <tbody>{filas_html_top_vacios}</tbody>

    </table>

</body>

</html>"""



    col_exp1, col_exp2, col_exp3 = st.columns(3)

    with col_exp1:

        st.download_button(

            label="📄 Descargar Informe Ejecutivo con Hipervínculos (HTML / Imprimible a PDF)",

            data=html_ejecutivo.encode("utf-8"),

            file_name="Informe_Ejecutivo_Auditoria_BIM_APV.html",

            mime="text/html",

            width="stretch"

        )

    with col_exp2:

        csv_matriz = grp_mod_exec[cols_matriz_exec].to_csv(index=False).encode("utf-8")

        st.download_button(

            label="📊 Descargar Matriz Ejecutiva por Modelo (CSV / Excel)",

            data=csv_matriz,

            file_name="Matriz_Calidad_Modelos_APV.csv",

            mime="text/csv",

            width="stretch"

        )

    with col_exp3:

        csv_vac_res = df_res_vacios.to_csv(index=False).encode("utf-8")

        st.download_button(

            label="📥 Descargar Resumen de los Parámetros APV (CSV / Excel)",

            data=csv_vac_res,

            file_name="Resumen_Parametros_BEP_APV.csv",

            mime="text/csv",

            width="stretch"

        )



# --- PESTAÑA 13 (NUEVA: CONTROL DE AVANCE MENSUAL Y NO-REGRESIÓN DE ENTREGAS) ---

with tab13:

    st.subheader("📈 13. Control de Avance Mensual y Regla de No-Regresión de Modelos")

    st.markdown(

        "**Regla de Negocio APV:** *El número de modelos IFC entregados jamás puede ser inferior al del mes anterior; "

        "siempre debe mantenerse igual o incrementarse conforme avanza la obra.*"

    )



    col_av1, col_av2, col_av3 = st.columns(3)

    diferencia_modelos = len(sel_archivos) - umbral_mes_anterior

    col_av1.metric("Modelos Entrega Mes Anterior (Base)", umbral_mes_anterior)

    col_av2.metric("Modelos Entrega Actual", len(sel_archivos), delta=f"{diferencia_modelos:+d} modelos")

    col_av3.metric(

        "Estado Regla de Avance",

        "✅ CUMPLE" if diferencia_modelos >= 0 else "🚨 INCUMPLE"

    )



    # Extraer disciplina y revisión de cada archivo actual

    desglose_rev = []

    for arch in sel_archivos:

        partes = str(arch)[:-4].split("_") if str(arch).lower().endswith(".ifc") else str(arch).split("_")

        disc_arch = partes[4].upper() if len(partes) > 4 else "SIN_DISC"

        rev_arch = partes[6].upper() if len(partes) > 6 else "SIN_REV"

        desglose_rev.append({

            "Archivo IFC": arch,

            "Disciplina (Bloque 5)": disc_arch,

            "Revisión Actual (Bloque 7)": rev_arch,

            "Elementos Auditados": int((df_original["Archivo_Origen"] == arch).sum())

        })

    df_rev = pd.DataFrame(desglose_rev)



    c_rev1, c_rev2 = st.columns(2)

    with c_rev1:

        fig_disc = px.bar(

            df_rev.groupby("Disciplina (Bloque 5)").size().reset_index(name="Cantidad Modelos"),

            x="Disciplina (Bloque 5)",

            y="Cantidad Modelos",

            text="Cantidad Modelos",

            title="Modelos IFC Entregados por Disciplina"

        )

        st.plotly_chart(fig_disc, width="stretch")

    with c_rev2:

        fig_revs = px.pie(

            df_rev,

            names="Revisión Actual (Bloque 7)",

            title="Distribución de Índices de Revisión (Bloque 7 BEP)",

            hole=0.4

        )

        st.plotly_chart(fig_revs, width="stretch")



    st.markdown("#### 🔍 Comparador Opcional de Listado de Modelos vs Mes Anterior")

    texto_modelos_mes_ant = st.text_area(

        "Si deseas comprobar qué archivos específicos entraron nuevos o cuáles faltan respecto al mes pasado, pega aquí los nombres de los IFC del mes anterior (uno por línea):",

        placeholder="V_N035_OB_SEG_MOD_EaPavBtMC12_01D.ifc\nV_N035_OB_MOD_EST_DmBlqGFarDN2_01D.ifc",

        height=120

    )

    if texto_modelos_mes_ant.strip():

        lista_ant = [x.strip() for x in texto_modelos_mes_ant.splitlines() if x.strip()]

        # Comparar por raíz sin revisión (primeros 6 bloques)

        def raiz_modelo(nombre):

            b = str(nombre)[:-4] if str(nombre).lower().endswith(".ifc") else str(nombre)

            p = b.split("_")

            return "_".join(p[:6]).upper() if len(p) >= 6 else b.upper()



        raices_ant = {raiz_modelo(x): x for x in lista_ant}

        raices_act = {raiz_modelo(x): x for x in sel_archivos}



        faltantes = [raices_ant[k] for k in raices_ant if k not in raices_act]

        nuevos = [raices_act[k] for k in raices_act if k not in raices_ant]



        if faltantes:

            st.error(f"🚨 **Faltan {len(faltantes)} modelos que estaban el mes anterior:** {', '.join(faltantes)}")

        else:

            st.success("✅ Todos los modelos del listado anterior están presentes en la entrega actual.")

        if nuevos:

            st.info(f"🆕 **Modelos nuevos incorporados en esta entrega ({len(nuevos)}):** {', '.join(nuevos)}")



# --- PESTAÑA 14 (NUEVA: AUDITORÍA CRUZADA DE COHERENCIA 4D / 5D / 6D) ---

with tab14:

    st.subheader("🏗️ 14. Auditoría de Coherencia Cruzada 4D (Planificación), 5D (Mediciones) y 6D/GIS")

    st.markdown(

        "Verifica que no existan incongruencias lógicas entre parámetros del mismo bloque "

        "(por ejemplo, elementos con **Medición** numérica pero sin **Unidad de Obra** o sin **Tipo de Medición**)."

    )



    reglas_coherencia = []



    # Regla 1 (5D): Tiene Medición pero falta Unidad de Obra o Tipo de Medición

    if all(c in df_original.columns for c in ["02_04_01_APV_MEDICION", "02_05_01_APV_UNIDAD-OBRA", "02_06_01_APV_TIPO-MED"]):

        tiene_med = (~mascara_vacio_rapida(df_original, "02_04_01_APV_MEDICION")) & (~mascara_comodin_rapida(df_original, "02_04_01_APV_MEDICION"))

        falta_uo_o_tmed = mascara_vacio_rapida(df_original, "02_05_01_APV_UNIDAD-OBRA") | mascara_vacio_rapida(df_original, "02_06_01_APV_TIPO-MED")

        m_inco_5d = (
            mask_arr
            & mascaras_parametro_modelo.get("02_04_01_APV_MEDICION", np.zeros(len(df_original), dtype=bool))
            & mascaras_parametro_modelo.get("02_05_01_APV_UNIDAD-OBRA", np.zeros(len(df_original), dtype=bool))
            & mascaras_parametro_modelo.get("02_06_01_APV_TIPO-MED", np.zeros(len(df_original), dtype=bool))
            & tiene_med & falta_uo_o_tmed
        )

        reglas_coherencia.append(("5D - Con Medición pero sin Unidad de Obra o Tipo-Med", m_inco_5d))



    # Regla 2 (4D): Tiene % Ejecutado pero falta Código o Nombre de Tarea

    if all(c in df_original.columns for c in ["04_08_APV_PORCENTAJE-EJECUTADO", "04_01_APV_CÓDIGO-TAREA", "04_02_APV_NOMBRE-TAREA"]):

        tiene_pct = (~mascara_vacio_rapida(df_original, "04_08_APV_PORCENTAJE-EJECUTADO")) & (~mascara_comodin_rapida(df_original, "04_08_APV_PORCENTAJE-EJECUTADO"))

        falta_tarea = mascara_vacio_rapida(df_original, "04_01_APV_CÓDIGO-TAREA") | mascara_vacio_rapida(df_original, "04_02_APV_NOMBRE-TAREA")

        m_inco_4d = (
            mask_arr
            & mascaras_parametro_modelo.get("04_08_APV_PORCENTAJE-EJECUTADO", np.zeros(len(df_original), dtype=bool))
            & mascaras_parametro_modelo.get("04_01_APV_CÓDIGO-TAREA", np.zeros(len(df_original), dtype=bool))
            & mascaras_parametro_modelo.get("04_02_APV_NOMBRE-TAREA", np.zeros(len(df_original), dtype=bool))
            & tiene_pct & falta_tarea
        )

        reglas_coherencia.append(("4D - Con % Ejecutado pero sin Código/Nombre de Tarea", m_inco_4d))



    # Regla 3 (6D): Tiene Plan de Mantenimiento pero falta Código de Mantenimiento

    if all(c in df_original.columns for c in ["08_01_APV_PLAN-MANTENIMIENTO", "08_03_APV_COD-MANTENIMIENTO"]):

        tiene_plan = (~mascara_vacio_rapida(df_original, "08_01_APV_PLAN-MANTENIMIENTO")) & (~mascara_comodin_rapida(df_original, "08_01_APV_PLAN-MANTENIMIENTO"))

        falta_cod_mant = mascara_vacio_rapida(df_original, "08_03_APV_COD-MANTENIMIENTO")

        m_inco_6d = (
            mask_arr
            & mascaras_parametro_modelo.get("08_01_APV_PLAN-MANTENIMIENTO", np.zeros(len(df_original), dtype=bool))
            & mascaras_parametro_modelo.get("08_03_APV_COD-MANTENIMIENTO", np.zeros(len(df_original), dtype=bool))
            & tiene_plan & falta_cod_mant
        )

        reglas_coherencia.append(("6D - Con Plan de Mantenimiento pero sin Código de Mantenimiento", m_inco_6d))



    res_coherencia = [

        {"Regla de Coherencia BEP": nombre_r, "Elementos Incoherentes": int(m_r.sum()), "Estado": "✅ OK" if int(m_r.sum()) == 0 else f"⚠️ Revisar ({int(m_r.sum()):,})"}

        for nombre_r, m_r in reglas_coherencia

    ]

    st.dataframe(pd.DataFrame(res_coherencia), width="stretch", hide_index=True)



    if reglas_coherencia:

        regla_sel_14 = st.selectbox(

            "Inspeccionar elementos que incumplen la regla:",

            options=[r[0] for r in reglas_coherencia],

            key="t14_regla_sel"

        )

        mask_sel_14 = dict(reglas_coherencia)[regla_sel_14]

        idx_14 = np.flatnonzero(mask_sel_14)

        if len(idx_14) > 0:

            cols_14 = [

                c for c in [

                    "Archivo_Origen", col_id_nativo, "GlobalId", "Clase_IFC",

                    "02_04_01_APV_MEDICION", "02_05_01_APV_UNIDAD-OBRA", "02_06_01_APV_TIPO-MED",

                    "04_01_APV_CÓDIGO-TAREA", "04_02_APV_NOMBRE-TAREA", "04_08_APV_PORCENTAJE-EJECUTADO"

                ] if c in df_original.columns

            ]

            st.dataframe(df_original[cols_14].iloc[idx_14[:5000]], width="stretch")

        else:

            st.success("✅ Cero incoherencias en esta regla para los modelos seleccionados.")



# --- PESTAÑA 15: DIAGNÓSTICO DE EXTRACCIÓN POR MODELO Y PARÁMETRO ---
with tab15:
    st.subheader("🧬 15. Diagnóstico de extracción y cobertura real en el Parquet")
    st.markdown(
        "Este módulo examina lo que **realmente contiene el Parquet** para un modelo concreto. "
        "No certifica por sí solo qué muestra Navisworks: ayuda a detectar diferencias entre la vista del cliente "
        "y los datos que recibió el dashboard. Un parámetro sin valores extraídos se marca como no verificable."
    )

    modelos_diag_disponibles = [a for a in sel_archivos if a in archivos_disp]
    if modelos_diag_disponibles:
        idx_diag = next(
            (i for i, a in enumerate(modelos_diag_disponibles) if "CoDrag2VLC" in str(a)),
            0
        )
        modelo_diag = st.selectbox(
            "Selecciona el modelo IFC que deseas investigar:",
            options=modelos_diag_disponibles,
            index=idx_diag,
            key="t15_modelo_diag"
        )
        df_modelo_diag = df_original.loc[
            df_original["Archivo_Origen"].astype(str) == str(modelo_diag)
        ]
        n_filas_diag = len(df_modelo_diag)
        mask_vacios_gid = (
            mascara_vacio_serie(df_modelo_diag["GlobalId"])
            if "GlobalId" in df_modelo_diag.columns
            else np.ones(n_filas_diag, dtype=bool)
        )
        params_oficiales_diag = PARAMETROS_APV if incluir_geo else PARAMS_NO_GEO
        resumen_diag_parametros = []
        for p in params_oficiales_diag:
            localizado = p in mapa_parametros_apv and p in df_original.columns
            columnas_origen = mapa_parametros_apv.get(p, [])
            if not localizado:
                n_con_valor = None
                n_vacios_diag = None
                n_guion_diag = None
                pct_cobertura_diag = None
                muestra_diag = ""
                estado_diag = "⚪ No localizado en el Parquet"
            else:
                serie_diag = df_modelo_diag[p]
                m_vacio_diag = mascara_vacio_serie(serie_diag)
                n_con_valor = int((~m_vacio_diag).sum())
                n_vacios_diag = n_filas_diag - n_con_valor if n_con_valor > 0 else None
                n_guion_diag = int(mascara_comodin_rapida(df_modelo_diag, p).sum())
                pct_cobertura_diag = round(100 * n_con_valor / n_filas_diag, 1) if n_filas_diag else None
                valores_muestra = (
                    serie_diag.loc[~m_vacio_diag].astype(str).drop_duplicates().head(4).tolist()
                )
                muestra_diag = " | ".join(valores_muestra)
                if n_con_valor == 0:
                    estado_diag = "⚪ Sin ningún valor extraído en este IFC · NO VERIFICABLE"
                elif n_vacios_diag:
                    estado_diag = "🟡 Hay valores y también vacíos observados"
                else:
                    estado_diag = "🟢 Todas las filas tienen algún valor"
            resumen_diag_parametros.append({
                "Parámetro APV oficial": p,
                "Estado de lectura": estado_diag,
                "Filas del modelo": n_filas_diag,
                "Filas con valor extraído": n_con_valor,
                "Vacíos observados (solo si es evaluable)": n_vacios_diag,
                "Valores '-'": n_guion_diag,
                "% Filas con valor": pct_cobertura_diag,
                "Columna(s) origen": " | ".join(map(str, columnas_origen)),
                "Ejemplos de valores extraídos": muestra_diag
            })
        df_diag_parametros = pd.DataFrame(resumen_diag_parametros)
        diag_texto = st.text_input(
            "Filtrar por nombre de parámetro, estado o ejemplo de valor:",
            key="t15_filtro_texto"
        )
        if diag_texto.strip():
            q_diag = diag_texto.strip()
            m_diag = pd.Series(False, index=df_diag_parametros.index)
            for c in ["Parámetro APV oficial", "Estado de lectura", "Columna(s) origen", "Ejemplos de valores extraídos"]:
                m_diag = m_diag | df_diag_parametros[c].astype(str).str.contains(q_diag, case=False, na=False)
            df_diag_mostrar = df_diag_parametros.loc[m_diag]
        else:
            df_diag_mostrar = df_diag_parametros

        n_param_con_dato = int((df_diag_parametros["Filas con valor extraído"].fillna(0) > 0).sum())
        n_param_no_local = int(df_diag_parametros["Estado de lectura"].str.contains("No localizado", na=False).sum())
        n_param_no_valor = int(df_diag_parametros["Estado de lectura"].str.contains("NO VERIFICABLE", na=False).sum())
        k15a, k15b, k15c, k15d = st.columns(4)
        k15a.metric("Filas del modelo en Parquet", f"{n_filas_diag:,}")
        k15b.metric("Parámetros con valores extraídos", f"{n_param_con_dato:,}")
        k15c.metric("Parámetros sin valores en este IFC", f"{n_param_no_valor:,}")
        k15d.metric("Parámetros no localizados globalmente", f"{n_param_no_local:,}")
        st.dataframe(df_diag_mostrar, width="stretch", hide_index=True, height=500)
        st.download_button(
            "⬇️ Descargar diagnóstico de extracción del modelo (CSV)",
            data=df_diag_parametros.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"Diagnostico_Extraccion_{re.sub(r'[^A-Za-z0-9_-]+', '_', str(modelo_diag))}.csv",
            mime="text/csv",
            key="t15_descargar_csv"
        )
        st.caption(
            "Interpretación: 'sin valores extraídos' no significa que el parámetro esté vacío en Navisworks; "
            "significa que este Parquet no contiene ningún valor no vacío para ese campo en este modelo."
        )
    else:
        st.info("Selecciona al menos un modelo en los filtros de la barra lateral.")


# --- PESTAÑA 16: AUDITORÍA DE DUPLICADOS E IDENTIFICADORES ---
with tab16:
    st.subheader("🔗 16. Auditoría independiente de GlobalId e ID_Elemento duplicados")
    st.markdown(
        "Esta pestaña revisa los registros tal como están almacenados en el Parquet, "
        "independientemente del filtro de unificación de duplicados. Los repetidos se listan para revisión; "
        "no se eliminan automáticamente porque algunos pueden tener una explicación de origen."
    )
    # Barrera defensiva para archivos históricos/cachés creados con una versión previa.
    # La fusión conserva el primer valor no vacío entre columnas con la misma etiqueta.
    df_ids_unicas = coalescer_columnas_duplicadas(df_original)
    df_ids_unicas = df_ids_unicas.loc[:, ~df_ids_unicas.columns.duplicated(keep="first")].copy()
    df_ids_base = df_ids_unicas.loc[df_ids_unicas["Archivo_Origen"].isin(sel_archivos)].copy()
    campo_id_dup = st.radio(
        "Identificador que deseas comprobar:",
        options=[c for c in ["GlobalId", "ID_Elemento"] if c in df_ids_base.columns],
        horizontal=True,
        key="t16_campo_id"
    ) if any(c in df_ids_base.columns for c in ["GlobalId", "ID_Elemento"]) else None

    if campo_id_dup:
        m_id_invalido = df_ids_base[campo_id_dup].isna().to_numpy() | _normalizar_serie_texto(
            df_ids_base[campo_id_dup]
        ).isin(VALORES_VACIOS_LOWER).to_numpy()
        n_id_sin_valor = int(m_id_invalido.sum())
        m_id_con_valor = ~m_id_invalido
        df_ids_con_valor = df_ids_base.loc[m_id_con_valor].copy()
        df_ids_con_valor["_Clave_ID"] = _normalizar_serie_texto(df_ids_con_valor[campo_id_dup]).str.upper()
        es_dup = df_ids_con_valor.duplicated(subset=["Archivo_Origen", "_Clave_ID"], keep=False)
        df_repetidos_id = df_ids_con_valor.loc[es_dup].copy()
        n_filas_duplicadas = len(df_repetidos_id)
        n_valores_duplicados = int(df_repetidos_id.groupby(["Archivo_Origen", "_Clave_ID"]).ngroups) if not df_repetidos_id.empty else 0

        d1, d2, d3 = st.columns(3)
        d1.metric("Registros examinados", f"{len(df_ids_base):,}")
        d2.metric("Registros con ID vacío", f"{n_id_sin_valor:,}")
        d3.metric("Registros implicados en duplicados", f"{n_filas_duplicadas:,}")
        st.caption(f"Valores identificadores repetidos por modelo: {n_valores_duplicados:,}.")
        if not df_repetidos_id.empty:
            # Asegurar nombres únicos también en la tabla derivada. Si el ID elegido
            # ya es GlobalId, no añadir la columna por segunda vez.
            df_repetidos_id = coalescer_columnas_duplicadas(df_repetidos_id)
            df_repetidos_id = df_repetidos_id.loc[:, ~df_repetidos_id.columns.duplicated(keep="first")].copy()
            candidatos = ["Archivo_Origen", campo_id_dup, "GlobalId", "ID_Elemento", "Clase_IFC", "Nombre"]
            cols_dup_show = []
            for nombre_col in candidatos:
                if nombre_col in df_repetidos_id.columns and nombre_col not in cols_dup_show:
                    cols_dup_show.append(nombre_col)
            df_repetidos_mostrar = df_repetidos_id.loc[:, cols_dup_show].copy()
            # Defensa final: sort_values falla si la lista de columnas o las etiquetas
            # están duplicadas; esta lista se mantiene estrictamente única.
            columnas_orden = []
            for nombre_col in ["Archivo_Origen", campo_id_dup]:
                if nombre_col in df_repetidos_mostrar.columns and nombre_col not in columnas_orden:
                    columnas_orden.append(nombre_col)
            if columnas_orden:
                try:
                    df_repetidos_mostrar = df_repetidos_mostrar.sort_values(by=columnas_orden)
                except (ValueError, KeyError):
                    # Mostrar el listado sin ordenar es preferible a bloquear toda la app.
                    pass
            df_repetidos_mostrar = df_repetidos_mostrar.head(10000)
            st.dataframe(
                df_repetidos_mostrar,
                width="stretch",
                hide_index=True,
                height=450
            )
            st.download_button(
                "⬇️ Descargar identificadores duplicados (CSV)",
                data=df_repetidos_mostrar.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"Duplicados_{campo_id_dup}_APV.csv",
                mime="text/csv",
                key="t16_descargar_duplicados"
            )
        else:
            st.success("No se detectan duplicados no vacíos para este identificador dentro de cada modelo seleccionado.")

        if "GlobalId" in df_ids_base.columns:
            df_gid_validos = df_ids_base.loc[
                ~df_ids_base["GlobalId"].isna()
                & ~_normalizar_serie_texto(df_ids_base["GlobalId"]).isin(VALORES_VACIOS_LOWER)
            ]
            gid_multi = (
                df_gid_validos.groupby("GlobalId")["Archivo_Origen"].agg(
                    Modelos="nunique",
                    Archivos=lambda x: " | ".join(pd.unique(x.astype(str)))
                ).reset_index()
            )
            gid_multi = gid_multi.loc[gid_multi["Modelos"] > 1]
            st.markdown("#### GlobalId que aparecen en varios archivos IFC")
            if not gid_multi.empty:
                st.warning(f"Se encontraron {len(gid_multi):,} GlobalId presentes en más de un modelo. Revisa si son referencias repetidas o duplicados de entrega.")
                st.dataframe(gid_multi, width="stretch", hide_index=True)
            else:
                st.success("No hay GlobalId no vacíos compartidos entre distintos modelos seleccionados.")
    else:
        st.info("No existe una columna GlobalId ni ID_Elemento que se pueda auditar en el Parquet.")


# --- PESTAÑA 17: COBERTURA POR BLOQUE DEL BEP Y MODELO ---
with tab17:
    st.subheader("🧭 17. Matriz de cobertura APV por modelo y bloque BEP")
    st.markdown(
        "Compara los bloques 01–10 entre modelos. Solo evalúa un parámetro en un modelo cuando el Parquet "
        "contiene al menos un valor para ese campo en ese modelo. Los campos sin ningún valor extraído se "
        "cuentan aparte como **no verificables**, para no convertir un problema de extracción en una alerta del 100 %."
    )
    filas_cobertura_bep = []
    for arch_cov in sel_archivos:
        m_arch_cov = mask_arr & (df_original["Archivo_Origen"].astype(str).to_numpy() == str(arch_cov))
        df_arch_cov = df_original.loc[m_arch_cov]
        n_arch_cov = len(df_arch_cov)
        if n_arch_cov == 0:
            continue
        for codigo_cov, nombre_bloque_cov in NOMBRES_GRUPOS_BEP.items():
            parametros_bloque = [
                p for p in params_auditar
                if re.match(r"^(\d{2})", str(p))
                and re.match(r"^(\d{2})", str(p)).group(1) == codigo_cov
            ]
            parametros_evaluables_bloque = [
                p for p in parametros_bloque
                if p in df_original.columns
                and int((~mascara_vacio_rapida(df_arch_cov, p)).sum()) > 0
            ]
            valores_bloque = sum(
                int((~mascara_vacio_rapida(df_arch_cov, p)).sum())
                for p in parametros_evaluables_bloque
            )
            n_params_eval_bloque = len(parametros_evaluables_bloque)
            n_celdas_eval_bloque = n_arch_cov * n_params_eval_bloque
            n_celdas_vacias_bloque = n_celdas_eval_bloque - valores_bloque
            pct_bloque = round(100 * valores_bloque / n_celdas_eval_bloque, 1) if n_celdas_eval_bloque else np.nan
            n_no_verificables_bloque = max(0, len(parametros_bloque) - n_params_eval_bloque)
            filas_cobertura_bep.append({
                "Archivo IFC": arch_cov,
                "Código Bloque": codigo_cov,
                "Bloque BEP": nombre_bloque_cov,
                "Elementos auditados": n_arch_cov,
                "Parámetros oficiales del bloque": len(parametros_bloque),
                "Parámetros evaluables en este modelo": n_params_eval_bloque,
                "Parámetros sin valor extraído (N/V)": n_no_verificables_bloque,
                "Celdas evaluables": n_celdas_eval_bloque,
                "Celdas con valor (incluye '-')": valores_bloque,
                "Vacíos observados": n_celdas_vacias_bloque if n_celdas_eval_bloque else None,
                "% Cobertura evaluable": pct_bloque
            })

    df_cobertura_bep = pd.DataFrame(filas_cobertura_bep)
    if not df_cobertura_bep.empty:
        codigos_filtro = st.multiselect(
            "Filtrar bloques BEP:",
            options=list(NOMBRES_GRUPOS_BEP.keys()),
            default=list(NOMBRES_GRUPOS_BEP.keys()),
            format_func=lambda x: f"{x} · {NOMBRES_GRUPOS_BEP.get(x, x)}",
            key="t17_bloques"
        )
        df_cobertura_mostrar = df_cobertura_bep.loc[df_cobertura_bep["Código Bloque"].isin(codigos_filtro)]
        st.dataframe(
            df_cobertura_mostrar.sort_values(["Archivo IFC", "Código Bloque"]),
            width="stretch",
            hide_index=True,
            height=500
        )
        pivot_cov = df_cobertura_bep.pivot(
            index="Archivo IFC", columns="Código Bloque", values="% Cobertura evaluable"
        )
        pivot_cov = pivot_cov.reindex(columns=[c for c in NOMBRES_GRUPOS_BEP if c in pivot_cov.columns])
        if not pivot_cov.empty and pivot_cov.notna().any().any():
            fig_cov = px.imshow(
                pivot_cov,
                aspect="auto",
                color_continuous_scale=["#ef4444", "#f59e0b", "#10b981"],
                zmin=0,
                zmax=100,
                text_auto=".1f",
                labels={"x": "Bloque BEP", "y": "Modelo IFC", "color": "Cobertura (%)"},
                title="Cobertura de campos evaluables por modelo y bloque (%)"
            )
            st.plotly_chart(fig_cov, width="stretch")
        st.download_button(
            "⬇️ Descargar matriz de cobertura por modelo y bloque (CSV)",
            data=df_cobertura_bep.to_csv(index=False).encode("utf-8-sig"),
            file_name="Cobertura_APV_Modelo_Bloque_BEP.csv",
            mime="text/csv",
            key="t17_descargar_cobertura"
        )
        st.caption(
            "Un porcentaje alto de cobertura indica que los campos evaluables contienen valores o el comodín '-'. "
            "No sustituye la validación de aplicabilidad por categoría IFC ni la comparación directa con Navisworks."
        )
    else:
        st.info("No hay suficientes registros de modelos seleccionados para generar la matriz de cobertura.")


print("[DIAG FIN] Dashboard de 17 pestañas renderizado con éxito", flush=True)