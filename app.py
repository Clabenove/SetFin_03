import os
import re
import gc
import time
import unicodedata
from datetime import datetime
import io
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

css_styles = "\n".join([
    "<style>",
    "@media print {",
    "    section[data-testid='stSidebar'],",
    "    header[data-testid='stHeader'],",
    "    div[data-testid='stToolbar'],",
    "    .stDownloadButton, .stButton,",
    "    div[data-testid='stChatInput'] { display: none !important; }",
    "    .main .block-container {",
    "        padding-top: 0.5rem !important; max-width: 100% !important;",
    "    }",
    "}",
    ".kpi-card {",
    "    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);",
    "    border: 1px solid #334155; border-radius: 10px;",
    "    padding: 16px; text-align: center;",
    "    box-shadow: 0 4px 6px rgba(0,0,0,0.2);",
    "}",
    ".kpi-title {",
    "    font-size: 0.85rem; color: #94a3b8; text-transform: uppercase;",
    "    letter-spacing: 0.05em; margin-bottom: 6px;",
    "}",
    ".kpi-value { font-size: 1.75rem; font-weight: 700; color: #f8fafc; }",
    ".kpi-sub { font-size: 0.8rem; color: #38bdf8; margin-top: 4px; }",
    "</style>"
])
st.markdown(css_styles, unsafe_allow_html=True)

st.title("📋 Dashboard Integral de Auditoría BIM - APV")

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
COMODINES_EXACTOS = ["-", " -", "- ", " - "]
VALORES_VACIOS_LOWER = {"", "nan", "none", "<na>", "null"}


def _normalizar_clave_param(texto):
    s = str(texto).strip()
    if ":" in s:
        s = s.split(":")[-1].strip()
    if "." in s and not re.search(r"\d,\d", s):
        partes_p = s.split(".")
        if any("APV" in p.upper() or re.match(r"^\d{2}", p) for p in partes_p):
            s = partes_p[-1].strip()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = s.upper().replace("-", "_").replace(" ", "_")
    s = re.sub(r"_+", "_", s)
    return s


def mascara_vacio_rapida(df_ref, col_name):
    if col_name not in df_ref.columns:
        return np.ones(len(df_ref), dtype=bool)
    s = df_ref[col_name]
    return s.isna().to_numpy() | s.isin(VACIOS_EXACTOS).to_numpy()


def mascara_comodin_rapida(df_ref, col_name):
    if col_name not in df_ref.columns:
        return np.zeros(len(df_ref), dtype=bool)
    return df_ref[col_name].isin(COMODINES_EXACTOS).to_numpy()


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
    puerto = (
        partes[0]
        if len(partes) > 0 and partes[0].upper() in ["V", "S", "G"]
        else "V"
    )
    contrato = "N035"
    fase = "OB"
    tipo = (
        partes[3]
        if len(partes) > 3 and re.match(r"^[A-Za-z]{3}$", partes[3])
        else "MOD"
    )
    disc = (
        partes[4]
        if len(partes) > 4 and re.match(r"^[A-Za-z]{3}$", partes[4])
        else "EST"
    )
    desc = (
        re.sub(r"[^A-Za-z0-9\-]", "", partes[5])
        if len(partes) > 5 else "Proyecto"
    )
    if not desc:
        desc = "Proyecto"
    rev = (
        partes[6]
        if len(partes) > 6 and re.match(r"^\d{2}[A-Za-z]$", partes[6])
        else "01A"
    )
    return (
        f"{puerto.upper()}_{contrato}_{fase}_"
        f"{tipo.upper()}_{disc.upper()}_{desc}_{rev.upper()}.ifc"
    )


def discernir_software_origen(sub_df_modelo):
    """
    Discierne si un modelo IFC proviene de Autodesk Revit o Autodesk Civil 3D
    analizando las clases IFC y nombres de elementos predominantes.
    """
    if sub_df_modelo.empty:
        return "Indeterminado"
    clases = sub_df_modelo["Clase_IFC"].dropna().astype(str).str.lower().tolist()
    nombres_str = " ".join(
        sub_df_modelo.get("Nombre", pd.Series(dtype=str)).dropna().astype(str).str.lower().head(200)
    )
    
    # Clases típicas de Civil 3D (infraestructura, alineaciones, terrenos, tuberías de obra civil)
    clases_civil = sum(1 for c in clases if any(k in c for k in ["alignment", "tin", "site", "geographic", "civil", "road", "pipe"]))
    # Clases típicas de Revit (edificación, muros, puertas, ventanas, pilares estructurales)
    clases_revit = sum(1 for c in clases if any(k in c for k in ["wall", "door", "window", "slab", "column", "beam", "roof"]))
    
    if "civil" in nombres_str or "surface" in nombres_str or clases_civil > clases_revit * 2:
        return "Autodesk Civil 3D"
    elif clases_revit > 0 or "revit" in nombres_str:
        return "Autodesk Revit"
    else:
        return "Desconocido / Genérico"


def discernir_tipo_modelo(nombre_archivo, sub_df_modelo):
    """
    Discierne la tipología y disciplina del modelo basándose en la nomenclatura BEP
    y el contenido semántico.
    """
    nombre_low = str(nombre_archivo).lower()
    if "geo" in nombre_low or "sondeo" in nombre_low or "terreno" in nombre_low:
        return "Geotecnia y Ensayos (09)"
    
    partes = str(nombre_archivo)[:-4].split("_") if nombre_low.endswith(".ifc") else nombre_archivo.split("_")
    disc = partes[4].upper() if len(partes) > 4 else "GEN"
    
    mapa_disc = {
        "EST": "Estructura y Cimentación",
        "ARQ": "Arquitectura y Acabados",
        "MEC": "Instalaciones Mecánicas / HVAC",
        "ELE": "Instalaciones Eléctricas",
        "SAN": "Saneamiento y Drenaje",
        "VIG": "Vialidad y Obras Liniales",
        "SEG": "Seguridad y Salud",
        "TOP": "Topografía y Movimiento de Tierras"
    }
    return mapa_disc.get(disc, f"Disciplina ({disc})")


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


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_PARQUET = os.path.join(BASE_DIR, "resumen_ifc_consolidado.parquet")

if not os.path.isfile(RUTA_PARQUET):
    st.error(f"No se encuentra el archivo: {RUTA_PARQUET}")
    st.stop()


@st.cache_resource(show_spinner="Cargando e indexando base de datos BIM...")
def inicializar_motor_apv(ruta):
    t0 = time.perf_counter()
    print("[DIAG 1] Leyendo archivo Parquet...", flush=True)
    df_raw = pd.read_parquet(ruta, engine="pyarrow")
    if df_raw.columns.duplicated().any():
        df_raw = df_raw.loc[:, ~df_raw.columns.duplicated()]

    mapa_norm_oficial = {_normalizar_clave_param(p): p for p in PARAMETROS_APV}
    mapa_sin_apv = {
        _normalizar_clave_param(p).replace("_APV_", "_"): p
        for p in PARAMETROS_APV
    }

    for c in list(df_raw.columns):
        if c in PARAMETROS_APV:
            continue
        cn = _normalizar_clave_param(c)
        target_p = mapa_norm_oficial.get(cn) or mapa_sin_apv.get(cn)
        if target_p:
            if target_p not in df_raw.columns:
                df_raw.rename(columns={c: target_p}, inplace=True)
            else:
                v_dest = mascara_vacio_rapida(df_raw, target_p)
                v_orig = mascara_vacio_rapida(df_raw, c)
                mask_rescue = v_dest & (~v_orig)
                if mask_rescue.any():
                    df_raw.loc[mask_rescue, target_p] = df_raw.loc[mask_rescue, c]

    n_filas = len(df_raw)
    print(
        f"[DIAG 2] Parquet cargado: {n_filas:,} filas x "
        f"{len(df_raw.columns)} cols en {time.perf_counter() - t0:.2f}s",
        flush=True
    )

    archivos_unicos = sorted(
        df_raw["Archivo_Origen"].dropna().unique().tolist()
    )
    arch_cat = pd.Categorical(
        df_raw["Archivo_Origen"], categories=archivos_unicos
    )
    arch_codes = arch_cat.codes
    n_arch = max(1, len(archivos_unicos))
    valid_arch_mask = arch_codes >= 0
    arch_codes_safe = np.where(valid_arch_mask, arch_codes, 0)

    pres_base = np.zeros(n_filas, dtype=np.uint8)
    vac_base = np.zeros(n_filas, dtype=np.uint8)
    vac_nw_base = np.zeros(n_filas, dtype=np.uint8)
    matriz_presencia_mod = pd.DataFrame(
        False, index=archivos_unicos, columns=PARAMETROS_APV
    )

    for col in PARAMS_NO_GEO:
        v = mascara_vacio_rapida(df_raw, col)
        no_v = ~v
        vac_base += v.astype(np.uint8)
        pres_base += no_v.astype(np.uint8)

        if no_v.any():
            conteo_por_mod = np.bincount(
                arch_codes_safe,
                weights=(no_v & valid_arch_mask),
                minlength=n_arch
            ) > 0
            matriz_presencia_mod[col] = conteo_por_mod
            existe_en_nw = conteo_por_mod[arch_codes_safe] & valid_arch_mask
            vac_nw_base += (v & existe_en_nw).astype(np.uint8)

    pres_geo = np.zeros(n_filas, dtype=np.uint8)
    vac_geo = np.zeros(n_filas, dtype=np.uint8)
    vac_nw_geo = np.zeros(n_filas, dtype=np.uint8)

    for col in PARAMS_GEO:
        v = mascara_vacio_rapida(df_raw, col)
        no_v = ~v
        vac_geo += v.astype(np.uint8)
        pres_geo += no_v.astype(np.uint8)

        if no_v.any():
            conteo_por_mod = np.bincount(
                arch_codes_safe,
                weights=(no_v & valid_arch_mask),
                minlength=n_arch
            ) > 0
            matriz_presencia_mod[col] = conteo_por_mod
            existe_en_nw = conteo_por_mod[arch_codes_safe] & valid_arch_mask
            vac_nw_geo += (v & existe_en_nw).astype(np.uint8)

    pres_all = pres_base + pres_geo
    vac_all = vac_base + vac_geo
    vac_nw_all = vac_nw_base + vac_nw_geo

    max_pres_por_mod = np.zeros(n_arch, dtype=np.uint8)
    np.maximum.at(max_pres_por_mod, arch_codes_safe, pres_all)
    max_pres_fila_arr = max_pres_por_mod[arch_codes_safe]

    print("[DIAG 3] Precalculando grupos APV por modelo...", flush=True)
    grupos_por_arch = {a: set() for a in archivos_unicos}
    for c in PARAMETROS_APV:
        if c in matriz_presencia_mod.columns:
            prefijo = c.split("_")[0] if "_" in c else ""
            mods_act = matriz_presencia_mod.index[matriz_presencia_mod[c]].tolist()
            for a in mods_act:
                grupos_por_arch[a].add(prefijo)

    info_grupos = []
    for arch in archivos_unicos:
        es_geo = "geo" in str(arch).lower()
        g_set = grupos_por_arch[arch]
        n_params_visibles_nw = (
            int(matriz_presencia_mod.loc[arch].sum())
            if arch in matriz_presencia_mod.index else 0
        )
        info_grupos.append({
            "Archivo IFC": arch,
            "Tipo de Modelo": (
                "Modelo de Geotecnia" if es_geo
                else "Modelo Estándar / Proyecto"
            ),
            "Grupos Teóricos (BEP)": 11 if es_geo else 9,
            "Grupos Totales Detectados": len(g_set),
            "Parámetros Visibles en Navisworks": n_params_visibles_nw,
            "Grupos Específicos Detectados": (
                ", ".join(sorted(list(g_set))) if g_set
                else "Ninguno (Extraer con convertidor_ifc.py optimizado)"
            )
        })
    df_grupos = pd.DataFrame(info_grupos)

    gc.collect()
    print(
        f"[DIAG 4] Motor completado en {time.perf_counter() - t0:.2f}s",
        flush=True
    )
    return (
        df_raw, archivos_unicos, df_grupos,
        pres_base, vac_base, pres_all, vac_all,
        vac_nw_base, vac_nw_all, matriz_presencia_mod,
        arch_codes_safe, max_pres_fila_arr
    )


(
    df_original, archivos_disp, df_informe_grupos,
    pres_base_arr, vac_base_arr, pres_all_arr, vac_all_arr,
    vac_nw_base_arr, vac_nw_all_arr, matriz_presencia_nw,
    arch_codes_global, max_pres_modelo_arr
) = inicializar_motor_apv(RUTA_PARQUET)

col_id_nativo = (
    "ID_Elemento" if "ID_Elemento" in df_original.columns else "GlobalId"
)

# --- BARRA LATERAL ---
st.sidebar.header("⚙ Filtros de Auditoría")

modo_real_navisworks = st.sidebar.checkbox(
    "🎯 Modo Real Navisworks (Filtrar solo parámetros visibles en Navisworks)",
    value=True,
    help=(
        "Evalúa cada modelo y elemento únicamente respecto a los parámetros "
        "APV que realmente existen y se visualizan en Navisworks."
    )
)

incluir_geo = st.sidebar.checkbox("Incluir Psets 09 (Geotecnia)", value=False)
params_base_lista = PARAMETROS_APV if incluir_geo else PARAMS_NO_GEO

ocultar_fantasmas = st.sidebar.checkbox(
    "Omitir sub-elementos fantasma (sin Pset APV completo en Navisworks)",
    value=True
)
unificar_duplicados = st.sidebar.checkbox(
    "Eliminar/Unificar elementos duplicados (priorizando fila llena)",
    value=False
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
        f"🚨 **Alerta de Regresión:** {len(sel_archivos)} modelos "
        f"(faltan {umbral_mes_anterior - len(sel_archivos)} vs mes anterior)."
    )

if not sel_archivos:
    st.warning("Selecciona al menos un modelo IFC en la barra lateral.")
    st.stop()

if len(sel_archivos) == len(archivos_disp):
    mask_arr = np.ones(len(df_original), dtype=bool)
else:
    mask_arr = df_original["Archivo_Origen"].isin(sel_archivos).to_numpy()

s_pres_arr = pres_all_arr if incluir_geo else pres_base_arr

if unificar_duplicados:
    orden_completitud = np.argsort(-s_pres_arr, kind="mergesort")
    df_temp_dup = df_original.iloc[orden_completitud][
        ["Archivo_Origen", "GlobalId"]
    ]
    dup_sorted = df_temp_dup.duplicated(keep="first").to_numpy()
    dup_arr = np.zeros(len(df_original), dtype=bool)
    dup_arr[orden_completitud] = dup_sorted
    mask_arr = mask_arr & (~dup_arr)

if modo_real_navisworks:
    s_vac_arr = vac_nw_all_arr if incluir_geo else vac_nw_base_arr
    sub_mat_nw = matriz_presencia_nw.loc[
        matriz_presencia_nw.index.intersection(sel_archivos),
        params_base_lista
    ]
    params_visibles_en_sel = sub_mat_nw.columns[sub_mat_nw.any(axis=0)].tolist()
    params_auditar = (
        params_visibles_en_sel
        if len(params_visibles_en_sel) > 0 else params_base_lista
    )
else:
    s_vac_arr = vac_all_arr if incluir_geo else vac_base_arr
    params_auditar = params_base_lista


def mascara_vacio_efectiva(df_ref, col_name):
    v_raw = mascara_vacio_rapida(df_ref, col_name)
    if not modo_real_navisworks or col_name not in matriz_presencia_nw.columns:
        return v_raw
    mod_tiene_col = matriz_presencia_nw[col_name].to_numpy(dtype=bool)
    return v_raw & mod_tiene_col[arch_codes_global]


df_arch_pres = pd.DataFrame({
    "arch": df_original["Archivo_Origen"].to_numpy()[mask_arr],
    "pres": s_pres_arr[mask_arr]
})
suma_arch = df_arch_pres.groupby("arch")["pres"].sum()
archivos_vacios = suma_arch[suma_arch == 0].index.tolist()

if modo_real_navisworks:
    umbral_min_fila = np.maximum(
        1, (max_pres_modelo_arr * 0.25).astype(np.uint8)
    )
    es_fantasma_arr = (s_pres_arr < umbral_min_fila) & (max_pres_modelo_arr > 0)
else:
    es_fantasma_arr = (s_pres_arr == 0)

n_fantasmas = int((es_fantasma_arr & mask_arr).sum())
if ocultar_fantasmas and n_fantasmas > 0:
    if (s_pres_arr[mask_arr] > 0).any():
        es_arch_vacio = (
            df_original["Archivo_Origen"].isin(archivos_vacios).to_numpy()
        )
        mask_arr = mask_arr & ((~es_fantasma_arr) | es_arch_vacio)
        st.sidebar.success(
            f"🧹 Se filtraron {n_fantasmas:,} sub-elementos sin Psets. "
            f"Auditando {int(mask_arr.sum()):,} objetos reales de Navisworks."
        )

if modo_real_navisworks:
    n_omitidos = len(params_base_lista) - len(params_auditar)
    st.sidebar.info(
        f"🎯 **Sincronizado con Navisworks:** Auditando los "
        f"**{len(params_auditar)} parámetros** visibles en Navisworks "
        f"(se omiten {n_omitidos} no exportados a estos IFC)."
    )

total_el = int(mask_arr.sum())
mask_tiene_vacios = mask_arr & (s_vac_arr > 0)
n_inc_total = int(mask_tiene_vacios.sum())

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
    df_pesos_global = pd.DataFrame(
        columns=["Archivo_Origen", "Peso_Archivo_MB"]
    )
    peso_total = 0.0

# --- LAS 15 PESTAÑAS ---
(
    tab1, tab2, tab3, tab4, tab5, tab6, tab7,
    tab8, tab9, tab10, tab11, tab12, tab13, tab14, tab15
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
    "💬 11. Asistente IA Generativo",
    "📄 12. Resumen Ejecutivo & PDF",
    "📈 13. Control Avance Mensual",
    "🏗️ 14. Coherencia 4D/5D/6D",
    "📥 15. Exportar Excel APV & Software"
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
        peso_raw = pd.to_numeric(
            row.get("Peso_Archivo_MB", 0.0), errors="coerce"
        )
        peso = 0.0 if pd.isna(peso_raw) else float(peso_raw)
        es_ifc_ok = (
            "IFC4" in str(esquema).upper()
            or "IFC2X3" in str(esquema).upper()
        )
        diag = diagnosticar_nombre_bep(arch)
        sugerencia = (
            sugerir_nombre_bep(arch) if "❌" in diag else "✅ Nombre Correcto"
        )
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
    st.dataframe(df_naming_t1, use_container_width=True)

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
    st.dataframe(df_geo, use_container_width=True)
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

# --- PESTAÑA 3 ---
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
    st.plotly_chart(fig_clases, use_container_width=True)

    mask_proxy = mask_arr & (
        df_original["Clase_IFC"].to_numpy() == "IfcBuildingElementProxy"
    )
    n_proxys = int(mask_proxy.sum())
    st.metric(
        "Elementos Genéricos Totales (IfcBuildingElementProxy)",
        f"{n_proxys:,}"
    )

    st.markdown("---")
    st.markdown(
        "#### 🔎 Buscador e Inspector de Entidades IFC / Proxies "
        "(Sobre el 100% de Elementos)"
    )
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
        default_clases_t3 = (
            ["IfcBuildingElementProxy"]
            if "IfcBuildingElementProxy" in clases_disp_t3
            else clases_disp_t3
        )
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
            df_original["GlobalId"].astype(str).str.contains(
                q_t3, case=False, na=False
            ).to_numpy()
            | df_original[col_id_nativo].astype(str).str.contains(
                q_t3, case=False, na=False
            ).to_numpy()
        )
        if "Nombre" in df_original.columns:
            m_txt_t3 = m_txt_t3 | (
                df_original["Nombre"].astype(str).str.contains(
                    q_t3, case=False, na=False
                ).to_numpy()
            )
        if "01_09_APV_NOMBRE" in df_original.columns:
            m_txt_t3 = m_txt_t3 | (
                df_original["01_09_APV_NOMBRE"].astype(str).str.contains(
                    q_t3, case=False, na=False
                ).to_numpy()
            )
        mask_filtro_t3 = mask_filtro_t3 & m_txt_t3

    idx_t3_all = np.flatnonzero(mask_filtro_t3)
    n_t3_match = len(idx_t3_all)

    if n_t3_match > 0:
        idx_t3_show = (
            idx_t3_all if limite_t3 == "Todas"
            else idx_t3_all[:int(limite_t3)]
        )
        cols_p = [
            c for c in [
                "Archivo_Origen", col_id_nativo, "GlobalId",
                "Clase_IFC", "Nombre", "01_09_APV_NOMBRE"
            ] if c in df_original.columns
        ]
        df_t3_view = df_original[cols_p].iloc[idx_t3_show]
        st.info(
            f"Mostrando **{len(df_t3_view):,}** de **{n_t3_match:,}** "
            "elementos que coinciden con tu filtro."
        )
        st.dataframe(df_t3_view, use_container_width=True, height=450)

        csv_t3 = (
            df_original[cols_p].iloc[idx_t3_all]
            .to_csv(index=False).encode("utf-8")
        )
        st.download_button(
            label=f"⬇️ Descargar los {n_t3_match:,} Elementos Filtrados (CSV)",
            data=csv_t3,
            file_name="Auditoria_APV_Integridad_IFC.csv",
            mime="text/csv",
            key="dl_t3_csv"
        )
    else:
        st.success(
            "✅ No se encontraron elementos con esos criterios en la Pestaña 3."
        )

# --- PESTAÑA 4 ---
with tab4:
    st.subheader(
        "4. Calidad de Formato (Estricto APV vs BEP) & Buscador por Modelo"
    )
    st.markdown(
        "El comodín **`-`** está permitido por el BEP y no genera error. "
        "Se audita el **100% de los elementos** (unidades, estados de obra, "
        "espacios en blanco y textos inválidos)."
    )

    @st.cache_data(show_spinner="Auditando formato en todos los elementos...")
    def obtener_errores_formato_vectorizado(
        _df_ref, params_audit, _mask_f, col_id_nat
    ):
        uni_validas = {"ud", "m", "m2", "dm3", "m3", "kg", "tn", "pa"}
        est_validos = {
            "Existente", "Demolido", "Temporal", "Proyectado", "Construido"
        }
        placeholders_malos = {
            "n/a", "na", "null", "none", "tbd",
            "sin definir", "por definir", "--", "."
        }

        lista_dfs = []
        for col in params_audit:
            if col not in _df_ref.columns:
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
                m_err = _mask_f & s_col.isin(list(mapa_err.keys())).to_numpy()
                if m_err.any():
                    idx_err = np.flatnonzero(m_err)
                    cols_base = [
                        "Archivo_Origen", col_id_nat, "GlobalId", col
                    ]
                    if "Clase_IFC" in _df_ref.columns:
                        cols_base.append("Clase_IFC")
                    sub_e = _df_ref[cols_base].iloc[idx_err].copy()
                    sub_e["Parámetro"] = col
                    sub_e["Infracción BEP"] = (
                        sub_e[col].map(mapa_err).fillna("Formato")
                    )
                    sub_e.rename(columns={
                        "Archivo_Origen": "Archivo",
                        col_id_nat: "ID_Elemento",
                        col: "Contenido Detectado"
                    }, inplace=True)
                    sub_e["Contenido Detectado"] = (
                        sub_e["Contenido Detectado"].astype(str)
                    )
                    cols_orden = [
                        "Archivo", "ID_Elemento", "GlobalId",
                        "Parámetro", "Contenido Detectado", "Infracción BEP"
                    ]
                    if "Clase_IFC" in sub_e.columns:
                        cols_orden.insert(3, "Clase_IFC")
                    lista_dfs.append(sub_e[cols_orden])

        if lista_dfs:
            return pd.concat(lista_dfs, ignore_index=True)
        return pd.DataFrame()

    df_err_fmt_total = obtener_errores_formato_vectorizado(
        df_original, params_auditar, mask_arr, col_id_nativo
    )

    if not df_err_fmt_total.empty:
        n_elem_fmt = df_err_fmt_total["GlobalId"].nunique()
        st.error(
            f"⚠️ Se detectaron **{len(df_err_fmt_total):,}** infracciones "
            f"de formato en **{n_elem_fmt:,}** elementos únicos."
        )

        c_f4_1, c_f4_2, c_f4_3, c_f4_4 = st.columns([2, 2, 2, 1])
        with c_f4_1:
            arch_err_disp = sorted(
                df_err_fmt_total["Archivo"].unique().tolist()
            )
            sel_arch_f4 = st.multiselect(
                "Filtrar por Modelo IFC:",
                arch_err_disp,
                default=arch_err_disp,
                key="f4_mod"
            )
        with c_f4_2:
            param_err_disp = sorted(
                df_err_fmt_total["Parámetro"].unique().tolist()
            )
            sel_param_f4 = st.multiselect(
                "Filtrar por Parámetro:",
                param_err_disp,
                default=param_err_disp,
                key="f4_par"
            )
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
                df_err_fmt_total["ID_Elemento"].astype(str).str.contains(
                    q_f4, case=False, na=False
                )
                | df_err_fmt_total["GlobalId"].astype(str).str.contains(
                    q_f4, case=False, na=False
                )
                | df_err_fmt_total["Contenido Detectado"].astype(str).str.contains(
                    q_f4, case=False, na=False
                )
                | df_err_fmt_total["Infracción BEP"].astype(str).str.contains(
                    q_f4, case=False, na=False
                )
            )

        df_f4_filtrado = df_err_fmt_total.loc[mask_f4]
        df_f4_show = (
            df_f4_filtrado if lim_f4 == "Todas"
            else df_f4_filtrado.iloc[:int(lim_f4)]
        )

        st.info(
            f"Mostrando **{len(df_f4_show):,}** de "
            f"**{len(df_f4_filtrado):,}** infracciones filtradas."
        )
        st.dataframe(df_f4_show, use_container_width=True, height=480)

        csv_f4 = df_f4_filtrado.to_csv(index=False).encode("utf-8")
        st.download_button(
            label=(
                f"⬇️ Descargar las {len(df_f4_filtrado):,} "
                "Infracciones de Formato Filtradas (CSV)"
            ),
            data=csv_f4,
            file_name="Auditoria_APV_Errores_Formato.csv",
            mime="text/csv",
            key="dl_f4_btn"
        )
    else:
        st.success(
            "✅ Todos los parámetros rellenos cumplen con el formato del BEP."
        )

# --- PESTAÑA 5 ---
with tab5:
    etiqueta_modo_t5 = (
        "(Visibles en Navisworks)"
        if modo_real_navisworks else "(Lista Teórica BEP)"
    )
    st.subheader(
        f"5. Auditoría Exclusiva de los {len(params_auditar)} "
        f"Parámetros Oficiales APV {etiqueta_modo_t5}"
    )
    st.markdown(
        "Si un parámetro contiene **`-`**, se valida como **Comodín BEP "
        "en Verde (`🟢`)**. En **Modo Real Navisworks**, cada parámetro se "
        "audita únicamente sobre los modelos que contienen dicho parámetro."
    )

    cols_ids_ref = df_original[[col_id_nativo, "GlobalId"]]
    resumen_params = []

    for p in params_auditar:
        es_vac_raw = mascara_vacio_rapida(df_original, p)
        es_com = mask_arr & mascara_comodin_rapida(df_original, p)
        es_dato = mask_arr & (~es_vac_raw) & (~es_com)
        es_vac = mask_arr & mascara_vacio_efectiva(df_original, p)

        n_vac = int(es_vac.sum())
        n_com = int(es_com.sum())
        n_datos = int(es_dato.sum())
        universo_param = max(1, n_datos + n_com + n_vac)
        pct_valido = (
            round(((n_datos + n_com) / universo_param) * 100, 1)
            if (n_datos + n_com + n_vac) > 0 else 100.0
        )

        if n_vac == 0 and n_com > 0 and n_datos == 0:
            estado_str = "🟢 Comodín BEP (-)"
            ids_faltantes, guids_faltantes = "-", "-"
        elif n_vac == 0:
            estado_str = "🟢 Completo en Navisworks"
            ids_faltantes, guids_faltantes = "-", "-"
        else:
            estado_str = f"🔴 Faltan {n_vac:,} elementos"
            idx_f = np.flatnonzero(es_vac)[:30]
            sub_f = cols_ids_ref.iloc[idx_f]
            sufijo = " ..." if n_vac > 30 else ""
            ids_faltantes = (
                ", ".join(sub_f[col_id_nativo].astype(str)) + sufijo
            )
            guids_faltantes = (
                ", ".join(sub_f["GlobalId"].astype(str)) + sufijo
            )

        resumen_params.append({
            "Parámetro Oficial APV": p,
            "Estado Auditoría": estado_str,
            "Con Dato Real": n_datos,
            "Con Comodín (-) Válido": n_com,
            "Vacíos (Error)": n_vac,
            "% Cumplimiento (Dato + '-')": pct_valido,
            "ID_Elemento Faltantes (Revit/C3D)": ids_faltantes,
            "GlobalId Faltantes (NWD/IFC)": guids_faltantes
        })
    df_res_vacios = pd.DataFrame(resumen_params)

    def colorear_estado(val):
        if "🟢" in str(val):
            return (
                "background-color: #d4edda; color: #155724; font-weight: bold;"
            )
        return "background-color: #f8d7da; color: #721c24; font-weight: bold;"

    st.dataframe(
        df_res_vacios.style.map(colorear_estado, subset=["Estado Auditoría"]),
        use_container_width=True
    )

    if n_inc_total > 0:
        st.markdown("---")
        st.markdown(
            "#### 🔍 Buscador Global e Inspector de Elementos con "
            f"Parámetros Vacíos (Total detectados: **{n_inc_total:,}**)"
        )
        st.caption(
            "💡 Este buscador filtra directamente sobre los "
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
            params_con_vacios = df_res_vacios.loc[
                df_res_vacios["Vacíos (Error)"] > 0, "Parámetro Oficial APV"
            ].tolist()
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

        mask_v5_search = (
            mask_tiene_vacios
            & df_original["Archivo_Origen"].isin(mod_sel_v5).to_numpy()
        )

        if param_esp_v5 != "TODOS (Cualquier parámetro vacío)":
            mask_v5_search = (
                mask_v5_search
                & mascara_vacio_efectiva(df_original, param_esp_v5)
            )

        if txt_buscar_v5.strip():
            q_v5 = txt_buscar_v5.strip()
            m_txt_v5 = (
                df_original["GlobalId"].astype(str).str.contains(
                    q_v5, case=False, na=False
                ).to_numpy()
                | df_original[col_id_nativo].astype(str).str.contains(
                    q_v5, case=False, na=False
                ).to_numpy()
                | df_original["Clase_IFC"].astype(str).str.contains(
                    q_v5, case=False, na=False
                ).to_numpy()
                | df_original["Archivo_Origen"].astype(str).str.contains(
                    q_v5, case=False, na=False
                ).to_numpy()
            )
            if "Nombre" in df_original.columns:
                m_txt_v5 = m_txt_v5 | (
                    df_original["Nombre"].astype(str).str.contains(
                        q_v5, case=False, na=False
                    ).to_numpy()
                )
            if "01_09_APV_NOMBRE" in df_original.columns:
                m_txt_v5 = m_txt_v5 | (
                    df_original["01_09_APV_NOMBRE"].astype(str).str.contains(
                        q_v5, case=False, na=False
                    ).to_numpy()
                )
            mask_v5_search = mask_v5_search & m_txt_v5

        idx_v5_all = np.flatnonzero(mask_v5_search)
        n_v5_encontrados = len(idx_v5_all)

        if n_v5_encontrados > 0:
            total_paginas_v5 = max(
                1, int(np.ceil(n_v5_encontrados / int(tam_pag_v5)))
            )
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
                    f"✅ Se encontraron **{n_v5_encontrados:,}** elementos. "
                    f"Mostrando filas **{inicio_v5 + 1:,}** a **{fin_v5:,}**."
                )

            cols_b = [
                c for c in [
                    "Archivo_Origen", col_id_nativo, "GlobalId",
                    "Clase_IFC", "Nombre", "01_09_APV_NOMBRE"
                ] if c in df_original.columns
            ]
            df_inc_view = df_original[cols_b].iloc[idx_inc].copy()
            df_inc_view["Cant_Vacios"] = s_vac_arr[idx_inc]

            params_disp = [
                p for p in params_auditar if p in df_original.columns
            ]
            sub_p = df_original[params_disp].iloc[idx_inc]
            mat_vac = sub_p.isna() | sub_p.isin(VACIOS_EXACTOS)
            if modo_real_navisworks:
                arch_sub = df_original["Archivo_Origen"].iloc[idx_inc].values
                mat_existe_mod = matriz_presencia_nw.loc[arch_sub, params_disp]
                mat_vac = mat_vac.values & mat_existe_mod.values
                mat_vac = pd.DataFrame(
                    mat_vac, index=sub_p.index, columns=params_disp
                )

            df_inc_view["Parámetros_Vacíos"] = mat_vac.apply(
                lambda r: ", ".join(r.index[r]), axis=1
            )
            st.dataframe(df_inc_view, use_container_width=True, height=500)

            col_dl1, col_dl2 = st.columns(2)
            with col_dl1:
                csv_pag_v5 = df_inc_view.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label=(
                        "⬇️ Descargar esta página con detalle de "
                        f"Parámetros Vacíos ({len(df_inc_view):,} filas CSV)"
                    ),
                    data=csv_pag_v5,
                    file_name=f"Elementos_Vacios_Pagina_{pag_v5}.csv",
                    mime="text/csv",
                    key="dl_v5_pag",
                    use_container_width=True
                )
            with col_dl2:
                df_all_v5_export = df_original[cols_b].iloc[idx_v5_all].copy()
                df_all_v5_export["Cant_Vacios"] = s_vac_arr[idx_v5_all]
                csv_all_v5 = (
                    df_all_v5_export.to_csv(index=False).encode("utf-8")
                )
                st.download_button(
                    label=(
                        f"⬇️ Descargar TODOS los {n_v5_encontrados:,} "
                        "IDs/GUIDs encontrados (CSV Completo)"
                    ),
                    data=csv_all_v5,
                    file_name="Auditoria_APV_Todos_Elementos_Vacios.csv",
                    mime="text/csv",
                    key="dl_v5_all",
                    use_container_width=True
                )
        else:
            st.warning(
                "⚠️ Ningún elemento con vacíos coincide con ese criterio."
            )
    else:
        st.success(
            "🎉 ¡Cero elementos con parámetros vacíos bajo la "
            "configuración actual de Navisworks!"
        )

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
            mask_nw = mask_arr & mascara_vacio_efectiva(
                df_original, param_filtro_nw
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
                    use_container_width=True
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
    c_s1.metric("Modelos IFC Analizados", len(archivos_disp))
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
        st.plotly_chart(fig_peso, use_container_width=True)
    else:
        c_s3.metric("Peso Consolidado de Modelos", "0.0 MB")

# --- PESTAÑA 8 ---
with tab8:
    st.subheader(
        "🚨 8. Alertas y Diagnóstico de IFCs por Modelo "
        "(Sincronizado con Navisworks)"
    )
    df_t8 = pd.DataFrame({
        "arch": df_original["Archivo_Origen"].loc[mask_arr],
        "tiene_vac": (s_vac_arr[mask_arr] > 0),
        "cant_vac": s_vac_arr[mask_arr],
        "cant_pres": s_pres_arr[mask_arr]
    })
    grp_t8 = df_t8.groupby("arch").agg(
        tot=("tiene_vac", "count"),
        elem_con_vac=("tiene_vac", "sum"),
        suma_vac=("cant_vac", "sum"),
        suma_pres=("cant_pres", "sum")
    )
    resumen_modelos_alt = []
    for arch in archivos_disp:
        tot = int(grp_t8.loc[arch, "tot"]) if arch in grp_t8.index else 0
        n_v_m = (
            int(grp_t8.loc[arch, "elem_con_vac"])
            if arch in grp_t8.index else 0
        )
        s_v_m = (
            int(grp_t8.loc[arch, "suma_vac"])
            if arch in grp_t8.index else 0
        )
        s_p_m = (
            int(grp_t8.loc[arch, "suma_pres"])
            if arch in grp_t8.index else 0
        )
        n_params_nw_mod = (
            int(matriz_presencia_nw.loc[arch, params_base_lista].sum())
            if arch in matriz_presencia_nw.index else 0
        )

        denom_celdas = max(1, s_p_m + s_v_m)
        pct_completitud_nw = (
            round((s_p_m / denom_celdas) * 100, 1)
            if (s_p_m + s_v_m) > 0 else 0.0
        )

        if tot == 0:
            est = "🚨 IFC Sin Elementos"
        elif s_p_m == 0:
            est = (
                "⚠️ Psets en Contenedor/Tipo no extraídos al Parquet "
                "(Usar convertidor_ifc.py optimizado)"
            )
        elif n_v_m == 0 or pct_completitud_nw >= 99.9:
            est = f"🟢 100% Completo en Navisworks ({n_params_nw_mod} params)"
        elif pct_completitud_nw >= 85.0:
            est = (
                f"🟢 {pct_completitud_nw}% Completo en Navisworks "
                f"({n_v_m:,} elem. con algún vacío)"
            )
        else:
            est = (
                f"🟡 {pct_completitud_nw}% Completo "
                f"({n_v_m:,} elem. con algún vacío)"
            )

        resumen_modelos_alt.append({
            "Archivo IFC": arch,
            "Elementos Auditados": tot,
            "Parámetros Visibles Navisworks": n_params_nw_mod,
            "% Completitud Navisworks": pct_completitud_nw,
            "Estado General": est
        })
    st.dataframe(pd.DataFrame(resumen_modelos_alt), use_container_width=True)

# --- PESTAÑA 9 ---
with tab9:
    st.subheader("📐 Grupos de parámetros")
    st.markdown(
        "Informe detallado por modelo sobre los bloques y grupos de "
        "parámetros detectados según la directriz del BEP "
        "(**Geotecnia = 11 grupos**; **Resto de modelos = 9 grupos**)."
    )
    st.dataframe(df_informe_grupos, use_container_width=True)

# --- PESTAÑA 10 ---
with tab10:
    st.subheader(
        "🔍 10. Ficha Detallada por Elemento "
        "(Inspector BIM Sincronizado con Navisworks)"
    )
    st.markdown(
        "Selecciona el archivo de origen (modelo IFC) mediante el desplegable, "
        "y luego **copia y pega o selecciona su `GlobalId` o `ID_Elemento`** "
        "para desplegar, auditar y editar sus parámetros APV."
    )

    modelos_disponibles_t10 = sorted(
        df_original.loc[mask_arr, "Archivo_Origen"].dropna().unique().tolist()
    )

    col_mod_sel, col_empty_10 = st.columns([2, 2])
    with col_mod_sel:
        archivo_seleccionado_t10 = st.selectbox(
            "1️⃣ Selecciona el Archivo de Origen (Modelo IFC):",
            options=["TODOS LOS MODELOS"] + modelos_disponibles_t10,
            index=0,
            key="select_ficha_archivo"
        )

    if archivo_seleccionado_t10 != "TODOS LOS MODELOS":
        df_filtrado_t10 = df_original.loc[
            mask_arr & (df_original["Archivo_Origen"] == archivo_seleccionado_t10)
        ]
    else:
        df_filtrado_t10 = df_original.loc[mask_arr]

    ids_disponibles_t10 = df_filtrado_t10["GlobalId"].dropna().unique()[:5000]

    col_sel10, col_paste10 = st.columns(2)
    with col_sel10:
        idx_default_10 = 0
        if "3H0KjjMnv619yNSGbFXGIK" in ids_disponibles_t10:
            idx_default_10 = int(
                np.where(ids_disponibles_t10 == "3H0KjjMnv619yNSGbFXGIK")[0][0]
            )
        id_seleccionado_lista = st.selectbox(
            "2️⃣ O selecciona un GlobalId de la lista:",
            options=(
                ids_disponibles_t10
                if len(ids_disponibles_t10) > 0 else ["No hay elementos"]
            ),
            index=idx_default_10 if len(ids_disponibles_t10) > 0 else 0,
            key="select_ficha_globalid"
        )
    with col_paste10:
        id_pegado_texto = st.text_input(
            "3️⃣ O copia y pega aquí cualquier GlobalId o ID_Elemento (editable):",
            value="",
            placeholder="Pega aquí ej: 3H0KjjMnv619yNSGbFXGIK o #168987",
            key="paste_ficha_id"
        )

    elem_df_match = pd.DataFrame()
    criterio_usado = ""

    if id_pegado_texto.strip():
        q10 = id_pegado_texto.strip()
        criterio_usado = q10
        m_exact = (
            (df_filtrado_t10["GlobalId"].astype(str) == q10)
            | (df_filtrado_t10[col_id_nativo].astype(str) == q10)
        )
        if m_exact.any():
            elem_df_match = df_filtrado_t10.loc[m_exact]
        else:
            m_part = (
                df_filtrado_t10["GlobalId"].astype(str).str.contains(
                    q10, case=False, na=False
                )
                | df_filtrado_t10[col_id_nativo].astype(str).str.contains(
                    q10, case=False, na=False
                )
            )
            elem_df_match = df_filtrado_t10.loc[m_part]
    elif len(ids_disponibles_t10) > 0 and id_seleccionado_lista != "No hay elementos":
        criterio_usado = str(id_seleccionado_lista)
        elem_df_match = df_filtrado_t10.loc[
            df_filtrado_t10["GlobalId"] == id_seleccionado_lista
        ]

    if not elem_df_match.empty:
        idx_match = elem_df_match.index
        orden_m = idx_match[np.argsort(-s_pres_arr[idx_match])]
        elem_df_match = df_original.loc[orden_m]

        if len(elem_df_match) > 1:
            st.info(
                f"🔎 Se encontraron **{len(elem_df_match)}** instancias "
                f"para `{criterio_usado}` (ordenada primero la más completa):"
            )
            opciones_desempate = [
                f"{r['GlobalId']} | ID: {r[col_id_nativo]} | {r['Archivo_Origen']}"
                for _, r in elem_df_match.head(50).iterrows()
            ]
            eleccion_desempate = st.selectbox(
                "Elegir coincidencia exacta:",
                opciones_desempate,
                key="t10_desempate"
            )
            guid_elegido = eleccion_desempate.split(" | ")[0]
            elem_info = elem_df_match.loc[
                elem_df_match["GlobalId"].astype(str) == guid_elegido
            ].iloc[0]
        else:
            elem_info = elem_df_match.iloc[0]

        guid_actual = elem_info.get("GlobalId", "N/A")
        arch_elem = elem_info.get("Archivo_Origen", "")

        if modo_real_navisworks and arch_elem in matriz_presencia_nw.index:
            params_ficha_elem = [
                p for p in params_base_lista
                if bool(matriz_presencia_nw.loc[arch_elem, p])
            ]
            if not params_ficha_elem:
                params_ficha_elem = params_auditar
        else:
            params_ficha_elem = params_auditar

        with st.expander(
            f"📋 Ficha Detallada del Elemento en Navisworks: {guid_actual}",
            expanded=True
        ):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                st.metric("Clase IFC", str(elem_info.get("Clase_IFC", "N/A")))
                st.metric("Archivo Origen", str(arch_elem))
            with col_f2:
                st.metric(
                    "ID Nativo (Revit/C3D)",
                    str(elem_info.get(col_id_nativo, "N/A"))
                )
                st.metric(
                    "Nombre Objeto",
                    str(elem_info.get(
                        "Nombre", elem_info.get("01_09_APV_NOMBRE", "N/A")
                    ))
                )
            with col_f3:
                n_vacios_elem = 0
                n_comodines_elem = 0
                n_datos_elem = 0
                filas_ficha = []
                for p in params_ficha_elem:
                    val_p = elem_info.get(p, np.nan)
                    es_v = (
                        pd.isna(val_p)
                        or str(val_p).strip() in VACIOS_EXACTOS
                    )
                    es_c = (
                        (not es_v)
                        and (str(val_p).strip() in COMODINES_EXACTOS)
                    )
                    if es_v:
                        n_vacios_elem += 1
                        est_p = "🔴 Vacío (Falta Dato)"
                    elif es_c:
                        n_comodines_elem += 1
                        est_p = "🟡 Comodín BEP (-)"
                    else:
                        n_datos_elem += 1
                        est_p = "🟢 Relleno en Navisworks (OK)"
                    filas_ficha.append({
                        "Grupo BEP": p.split("_")[0],
                        "Parámetro BEP": p,
                        "Valor en Navisworks": (
                            "" if pd.isna(val_p) else str(val_p)
                        ),
                        "Estado": est_p
                    })
                pct_obj = round(
                    ((n_datos_elem + n_comodines_elem)
                     / max(1, len(params_ficha_elem))) * 100,
                    1
                )
                st.metric(
                    "Parámetros Vacíos (Navisworks)",
                    n_vacios_elem,
                    delta=f"{pct_obj}% Cumplimiento",
                    delta_color="inverse"
                )
                st.caption(
                    f"🟢 Con dato: **{n_datos_elem}** | "
                    f"🟡 Comodín (-): **{n_comodines_elem}** | "
                    f"🔴 Vacíos: **{n_vacios_elem}**"
                )

            st.markdown(
                "##### 📊 Auditoría Individual de Parámetros "
                "(Vista Real Navisworks):"
            )
            filtro_vista_ficha = st.radio(
                "Filtrar parámetros de la ficha:",
                options=[
                    "🟢 Solo Parámetros Rellenos / Comodín (Visibles en Navisworks)",
                    "Todos los Parámetros del Modelo",
                    "🔴 Solo Parámetros Vacíos (Que Fallan)"
                ],
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
                    return (
                        "background-color: #f8d7da; color: #721c24; "
                        "font-weight: bold;"
                    )
                if "🟡" in str(val):
                    return (
                        "background-color: #fff3cd; color: #856404; "
                        "font-weight: bold;"
                    )
                return (
                    "background-color: #d4edda; color: #155724; "
                    "font-weight: bold;"
                )

            st.dataframe(
                df_ficha.style.map(estilo_fila_ficha, subset=["Estado"]),
                use_container_width=True,
                hide_index=True,
                height=450
            )
    else:
        st.error(
            f"❌ No se encontró ningún elemento con el identificador "
            f"`{criterio_usado}` en el modelo seleccionado."
        )

# --- PESTAÑA 11 ---
with tab11:
    st.subheader("💬 11. Asistente IA Generativo & Análisis Complejos - APV")
    st.markdown(
        "Haz consultas complejas en lenguaje natural: pídele **tablas comparativas "
        "entre modelos, análisis de criticidad de parámetros, auditorías cruzadas, "
        "diagnósticos de rendimiento o planes de acción**."
    )

    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": (
                    f"¡Hola Claudia! Estoy conectado al motor analítico de los "
                    f"**{len(sel_archivos)} modelos IFC** (**{total_el:,} "
                    "elementos sincronizados con Navisworks**). "
                    "Ahora puedes pedirme análisis complejos y tablas comparativas. Prueba con:\n"
                    "- *Hazme una tabla comparativa del porcentaje de cumplimiento y software origen.*\n"
                    "- *Realiza un análisis crítico de los 5 parámetros que más fallan y su impacto.*\n"
                    "- *Compárame el estado de los bloques de costes (5D) frente a planificación (4D).*\n"
                    "- *¿Qué recomendaciones me das para corregir los modelos con peor puntuación?*"
                )
            }
        ]

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    if prompt := st.chat_input(
        "Escribe tu consulta compleja o pídele una tabla comparativa..."
    ):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            p_low = prompt.lower()
            top_vacios_ia = df_res_vacios.sort_values(
                "Vacíos (Error)", ascending=False
            ).head(5)

            if any(k in p_low for k in ["tabla", "comparativa", "comparativo", "compara"]):
                df_comp_ia = grp_mod_exec.sort_values("% Cumplimiento BEP", ascending=False)
                markdown_table = "| Modelo IFC | Dictamen | Software Origen | Elementos | % Cumplimiento |\n| :--- | :--- | :--- | :---: | :---: |\n"
                for _, r in df_comp_ia.iterrows():
                    sub_m = df_original.loc[df_original["Archivo_Origen"] == r["Archivo_Origen"]]
                    soft_orig = discernir_software_origen(sub_m)
                    markdown_table += f"| `{r['Archivo_Origen']}` | {r['Dictamen Técnico']} | {soft_orig} | {r['Elementos']:,} | **{r['% Cumplimiento BEP']}%** |\n"
                
                respuesta = (
                    "### 📊 Tabla Comparativa Generativa de Modelos IFC\n"
                    f"A continuación, presento la comparativa analítica de los **{len(sel_archivos)} modelos activos** "
                    "con detección de software de autoría:\n\n"
                    f"{markdown_table}\n\n"
                    "💡 *Análisis generativo:* Los modelos con menor porcentaje requieren revisión de exportación de Property Sets en origen."
                )

            elif any(k in p_low for k in ["analisis", "análisis", "critico", "crítico", "impacto", "riesgo"]):
                lineas_p = "\n".join([
                    f"1. **`{r['Parámetro Oficial APV']}`**: Presenta **{r['Vacíos (Error)']:,} elementos vacíos** "
                    f"(Cumplimiento del **{r['% Cumplimiento (Dato + '-')']}%**). "
                    "Su ausencia bloquea la validación automatizada en fase de obra."
                    for _, r in top_vacios_ia.iterrows()
                ])
                respuesta = (
                    "### 🔬 Análisis Complejo de Criticidad de Parámetros\n"
                    "Tras auditar el flujo de datos y la presencia en Navisworks, este es el diagnóstico de los "
                    "**5 puntos más críticos** que ponen en riesgo el cumplimiento del BEP APV:\n\n"
                    f"{lineas_p}\n\n"
                    "**Plan de Mitigación Recomendado:**\n"
                    "- Exigir a las subcontratas la cumplimentación mediante plantillas de parámetros compartidos.\n"
                    "- Utilizar los conjuntos de selección XML (Pestaña 6) para aislar estos elementos en Navisworks."
                )

            elif "codrag" in p_low or "drag2vlc" in p_low:
                respuesta = (
                    "### 🔍 Informe Específico: Modelo CoDrag2VLC\n"
                    "Sobre el modelo **`CoDrag2VLC`**: en Navisworks sus parámetros se visualizan correctamente porque "
                    "el software hereda los valores desde el **Tipo (`IfcTypeObject`)** y el **Contenedor Padre**. "
                    "Si detectas discrepancias, recuerda procesarlo con el script optimizado `convertidor_ifc.py`."
                )

            elif any(k in p_low for k in ["proxy", "proxies", "generico", "genérico"]):
                respuesta = (
                    "### 🧱 Auditoría de Elementos Genéricos (IfcBuildingElementProxy)\n"
                    f"Actualmente se detectan **{n_proxys:,} elementos** clasificados como `IfcBuildingElementProxy` "
                    "en los modelos seleccionados.\n\n"
                    "**Impacto BIM:** Un volumen elevado de proxies reduce la semántica del modelo y dificulta la extracción "
                    "automatizada de mediciones (5D). Se recomienda reclasificar estos elementos a sus clases IFC nativas."
                )

            elif any(k in p_low for k in ["recomendacion", "recomendación", "consejo", "mejorar", "corregir"]):
                respuesta = (
                    "### 💡 Recomendaciones Estratégicas para la Dirección BIM\n"
                    f"1. **Control de Naming:** Asegurar que el 100% de los archivos cumplan con el Anejo 02 (Pestaña 1).\n"
                    f"2. **Mitigación de Vacíos:** Atacar de forma prioritaria los parámetros del Top 5 identificados (Pestaña 5).\n"
                    f"3. **Regla de Avance:** Actualmente mantienes **{len(sel_archivos)} modelos** frente al umbral de "
                    f"**{umbral_mes_anterior}**, cumpliendo con la política de no-regresión.\n"
                    "4. **Exportación IFC:** Verificar que todas las exportaciones desde Revit o Civil 3D incluyan los Property Sets de la APV."
                )

            else:
                pct_global_ia = (
                    round(
                        float(df_res_vacios["% Cumplimiento (Dato + '-')"].mean()),
                        1
                    )
                    if not df_res_vacios.empty else 0.0
                )
                respuesta = (
                    "**🤖 Asistente Generativo APV (Modo Análisis Avanzado):**\n"
                    f"He procesado tu solicitud cruzando los datos en vivo:\n"
                    f"- **Modelos analizados:** {len(sel_archivos)} archivos ({round(peso_total, 2)} MB)\n"
                    f"- **Objetos BIM evaluados:** {total_el:,} elementos\n"
                    f"- **Índice de cumplimiento medio:** {pct_global_ia}%\n"
                    f"- **Infracciones de formato:** {len(df_err_fmt_total):,}\n\n"
                    "💬 *Puedes pedirme explícitamente:* `Hazme una tabla comparativa de los modelos` o `Analiza los riesgos de los parámetros vacíos`."
                )

            st.markdown(respuesta)
            st.session_state.messages.append(
                {"role": "assistant", "content": respuesta}
            )

# --- PESTAÑA 12 ---
with tab12:
    fecha_actual_str = datetime.now().strftime("%d/%m/%Y %H:%M")
    st.subheader(
        "📄 12. Resumen Ejecutivo de Dirección & Exportación Interactiva - APV"
    )
    st.caption(
        "Autoridad Portuaria de Valencia (APV) · Contrato N035 · "
        f"Fecha de emisión: {fecha_actual_str}"
    )

    total_celdas_datos = int(df_res_vacios["Con Dato Real"].sum())
    total_celdas_comodin = int(df_res_vacios["Con Comodín (-) Válido"].sum())
    total_celdas_vacias = int(df_res_vacios["Vacíos (Error)"].sum())
    total_celdas_auditadas = max(
        1, total_celdas_datos + total_celdas_comodin + total_celdas_vacias
    )
    pct_cumplimiento_global = round(
        ((total_celdas_datos + total_celdas_comodin) / total_celdas_auditadas)
        * 100,
        1
    )

    n_naming_ok = sum(
        1 for r in res_naming
        if "✅" in r["Cumple Nomenclatura BEP (y Razón Exacta)"]
    )
    pct_naming_ok = round((n_naming_ok / max(1, len(res_naming))) * 100, 1)

    geo_consistente = not (
        len(df_geo) > 1
        and (
            df_geo["Origen Site X"].nunique() > 1
            or df_geo["Origen Site Y"].nunique() > 1
        )
    )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    with k1:
        st.markdown(
            '<div class="kpi-card"><div class="kpi-title">Modelos IFC</div>'
            f'<div class="kpi-value">{len(sel_archivos)}</div>'
            f'<div class="kpi-sub">Umbral mes ant: {umbral_mes_anterior}'
            '</div></div>',
            unsafe_allow_html=True
        )
    with k2:
        st.markdown(
            '<div class="kpi-card"><div class="kpi-title">Elementos BIM</div>'
            f'<div class="kpi-value">{total_el:,}</div>'
            '<div class="kpi-sub">Objetos Navisworks</div></div>',
            unsafe_allow_html=True
        )
    with k3:
        st.markdown(
            '<div class="kpi-card"><div class="kpi-title">Cumplimiento BEP</div>'
            f'<div class="kpi-value">{pct_cumplimiento_global}%</div>'
            '<div class="kpi-sub">Real en Navisworks</div></div>',
            unsafe_allow_html=True
        )
    with k4:
        st.markdown(
            '<div class="kpi-card"><div class="kpi-title">Naming Anejo 02</div>'
            f'<div class="kpi-value">{pct_naming_ok}%</div>'
            f'<div class="kpi-sub">{n_naming_ok}/{len(res_naming)} OK</div></div>',
            unsafe_allow_html=True
        )
    with k5:
        est_geo_kpi = "100% OK" if geo_consistente else "ALERTA"
        st.markdown(
            '<div class="kpi-card"><div class="kpi-title">Georreferenciación</div>'
            f'<div class="kpi-value">{est_geo_kpi}</div>'
            '<div class="kpi-sub">ETRS89 / IfcSite</div></div>',
            unsafe_allow_html=True
        )
    with k6:
        st.markdown(
            '<div class="kpi-card"><div class="kpi-title">Peso Consolidado</div>'
            f'<div class="kpi-value">{round(peso_total, 1)} MB</div>'
            f'<div class="kpi-sub">{n_proxys:,} Proxies</div></div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)

    df_mod_stats = pd.DataFrame({
        "Archivo_Origen": df_original["Archivo_Origen"].to_numpy()[mask_arr],
        "vac_count": s_vac_arr[mask_arr],
        "pres_count": s_pres_arr[mask_arr],
        "es_proxy": (
            df_original["Clase_IFC"].to_numpy()[mask_arr]
            == "IfcBuildingElementProxy"
        )
    })
    grp_mod_exec = df_mod_stats.groupby("Archivo_Origen").agg(
        Elementos=("vac_count", "count"),
        Elem_Con_Vacios=("vac_count", lambda x: int((x > 0).sum())),
        Suma_Celdas_Vacias=("vac_count", "sum"),
        Suma_Celdas_Llenas=("pres_count", "sum"),
        Proxies=("es_proxy", "sum")
    ).reset_index()

    grp_mod_exec["Total_Celdas_Modelo"] = (
        grp_mod_exec["Suma_Celdas_Llenas"] + grp_mod_exec["Suma_Celdas_Vacias"]
    ).replace(0, 1)
    grp_mod_exec["% Cumplimiento BEP"] = (
        (grp_mod_exec["Suma_Celdas_Llenas"] / grp_mod_exec["Total_Celdas_Modelo"])
        * 100
    ).round(1)
    grp_mod_exec["% Vacíos"] = (
        100.0 - grp_mod_exec["% Cumplimiento BEP"]
    ).round(1)
    grp_mod_exec["Naming BEP"] = grp_mod_exec["Archivo_Origen"].apply(
        lambda a: "✅ OK" if "✅" in diagnosticar_nombre_bep(a) else "❌ Error"
    )

    def dictamen_modelo(row):
        if row["Suma_Celdas_Llenas"] == 0:
            return "⚪ PSETS EN PADRE/TIPO (REEXTRAER PARQUET)"
        if row["% Cumplimiento BEP"] >= 95 and row["Naming BEP"] == "✅ OK":
            return "🟢 APTO"
        if row["% Cumplimiento BEP"] >= 75:
            return "🟡 CON OBSERVACIONES"
        return "🔴 REQUIERE CORRECCIÓN"

    grp_mod_exec["Dictamen Técnico"] = grp_mod_exec.apply(
        dictamen_modelo, axis=1
    )

    col_g1, col_g2 = st.columns([1.1, 1.9])
    with col_g1:
        df_donut = pd.DataFrame({
            "Estado de Celdas BEP": [
                "Con Dato Real", "Comodín BEP (-)", "Vacíos (Incumplimiento)"
            ],
            "Cantidad": [
                total_celdas_datos, total_celdas_comodin, total_celdas_vacias
            ]
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
            title="Balance Global de Celdas Auditadas (Navisworks)"
        )
        fig_donut.update_traces(
            textposition="inside", textinfo="percent+label"
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_g2:
        df_rank_mod = grp_mod_exec.sort_values(
            "% Cumplimiento BEP", ascending=True
        )
        fig_rank = px.bar(
            df_rank_mod,
            y="Archivo_Origen",
            x=["% Cumplimiento BEP", "% Vacíos"],
            orientation="h",
            title="Índice de Cumplimiento Real en Navisworks por Modelo (%)",
            color_discrete_map={
                "% Cumplimiento BEP": "#10b981", "% Vacíos": "#ef4444"
            },
            text_auto=".1f"
        )
        fig_rank.update_layout(
            barmode="stack",
            xaxis_title="% de Parámetros en Navisworks",
            yaxis_title="Modelo IFC"
        )
        st.plotly_chart(fig_rank, use_container_width=True)

    col_g3, col_g4 = st.columns(2)
    with col_g3:
        df_res_vacios["Codigo_Grupo"] = (
            df_res_vacios["Parámetro Oficial APV"].apply(
                lambda x: (
                    x.split("-")[0]
                    if "-" in x.split("_")[0] else x.split("_")[0]
                )
            )
        )
        df_res_vacios["Nombre_Bloque_BEP"] = (
            df_res_vacios["Codigo_Grupo"].map(NOMBRES_GRUPOS_BEP).fillna("Otros")
        )
        grp_bloques = df_res_vacios.groupby(
            "Nombre_Bloque_BEP", as_index=False
        )["% Cumplimiento (Dato + '-')"].mean()
        grp_bloques["% Cumplimiento Medio"] = (
            grp_bloques["% Cumplimiento (Dato + '-')"].round(1)
        )

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
        st.plotly_chart(fig_bloques, use_container_width=True)

    with col_g4:
        df_top_crit = (
            df_res_vacios.sort_values("Vacíos (Error)", ascending=False)
            .head(12)
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
        st.plotly_chart(fig_pareto, use_container_width=True)

    st.markdown("#### 🚦 Matriz Ejecutiva de Calidad por Modelo IFC")
    cols_matriz_exec = [
        "Archivo_Origen", "Dictamen Técnico", "Naming BEP", "Elementos",
        "Elem_Con_Vacios", "Proxies", "% Cumplimiento BEP"
    ]
    st.dataframe(
        grp_mod_exec[cols_matriz_exec].sort_values(
            "% Cumplimiento BEP", ascending=False
        ),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")
    st.markdown(
        "#### 🚀 Centro de Descarga de Informe Ejecutivo "
        "(PDF / HTML / Excel)"
    )

    filas_html_modelos = "".join([
        f"<tr><td>{r['Archivo_Origen']}</td>"
        f"<td><b>{r['Dictamen Técnico']}</b></td>"
        f"<td>{r['Naming BEP']}</td><td>{r['Elementos']:,}</td>"
        f"<td>{r['Elem_Con_Vacios']:,}</td><td>{int(r['Proxies']):,}</td>"
        f"<td><b>{r['% Cumplimiento BEP']}%</b></td></tr>"
        for _, r in grp_mod_exec.sort_values(
            "% Cumplimiento BEP", ascending=False
        ).iterrows()
    ])
    filas_html_bloques = "".join([
        f"<tr><td>{r['Nombre_Bloque_BEP']}</td>"
        f"<td><b>{r['% Cumplimiento Medio']}%</b></td></tr>"
        for _, r in grp_bloques.sort_values("Nombre_Bloque_BEP").iterrows()
    ])
    filas_html_top_vacios = "".join([
        f"<tr><td>{r['Parámetro Oficial APV']}</td>"
        f"<td>{r['Estado Auditoría']}</td>"
        f"<td>{r['Con Dato Real']:,}</td>"
        f"<td>{r['Con Comodín (-) Válido']:,}</td>"
        f"<td><b>{r['Vacíos (Error)']:,}</b></td>"
        f"<td><b>{r['% Cumplimiento (Dato + \'-\')']}%</b></td></tr>"
        for _, r in df_res_vacios.sort_values(
            "Vacíos (Error)", ascending=False
        ).head(25).iterrows()
    ])

    est_geo_txt = "OK" if geo_consistente else "Revisar"
    html_lineas = [
        "<!DOCTYPE html><html lang='es'><head><meta charset='UTF-8'>",
        "<title>Informe Ejecutivo Auditoría BIM - APV</title>",
        "<style>",
        "body { font-family: 'Segoe UI', Arial, sans-serif; margin: 32px; "
        "color: #1e293b; background: #f8fafc; }",
        ".header { background: #0f172a; color: white; padding: 24px 32px; "
        "border-radius: 12px; margin-bottom: 20px; display: flex; "
        "justify-content: space-between; align-items: center; }",
        ".nav { background: #e2e8f0; padding: 12px 20px; border-radius: 8px; "
        "margin-bottom: 24px; display: flex; gap: 18px; flex-wrap: wrap; }",
        ".nav a { color: #0284c7; font-weight: 600; text-decoration: none; }",
        ".btn-print { background: #0284c7; color: white; border: none; "
        "padding: 10px 18px; border-radius: 6px; cursor: pointer; "
        "font-weight: bold; }",
        ".kpis { display: grid; grid-template-columns: repeat(6, 1fr); "
        "gap: 12px; margin-bottom: 24px; }",
        ".kpi { background: white; border: 1px solid #cbd5e1; "
        "border-radius: 8px; padding: 14px; text-align: center; }",
        ".kpi h4 { margin: 0; font-size: 12px; color: #64748b; }",
        ".kpi p { margin: 6px 0 0 0; font-size: 22px; font-weight: 700; }",
        "table { width: 100%; border-collapse: collapse; background: white; "
        "margin-bottom: 28px; font-size: 13px; }",
        "th, td { border: 1px solid #cbd5e1; padding: 8px 12px; "
        "text-align: left; }",
        "th { background: #0f172a; color: white; }",
        "tr:nth-child(even) { background: #f1f5f9; }",
        "h2 { color: #0f172a; border-bottom: 2px solid #0284c7; "
        "padding-bottom: 6px; margin-top: 28px; }",
        "@media print { .no-print { display: none !important; } }",
        "</style></head><body>",
        "<div class='header'><div>",
        "<h1 style='margin:0; font-size:24px;'>"
        "📋 Acta Ejecutiva de Auditoría BIM & Cumplimiento BEP</h1>",
        f"<p style='margin:4px 0 0 0; color:#94a3b8;'>"
        f"Autoridad Portuaria de Valencia (APV) · Emitido: {fecha_actual_str}</p>",
        "</div><button class='btn-print no-print' onclick='window.print()'>"
        "🖨️ Imprimir / Guardar en PDF</button></div>",
        "<div class='nav no-print'><b>🔗 Índice Rápido:</b>",
        "<a href='#seccion-kpis'>1. KPIs Ejecutivos</a>",
        "<a href='#seccion-matriz'>2. Matriz por Modelo IFC</a>",
        "<a href='#seccion-bloques'>3. Cumplimiento por Bloques BEP</a>",
        "<a href='#seccion-criticos'>4. Top Parámetros Críticos</a>",
        "<a href='https://ausep2.streamlit.app/' target='_blank'>"
        "🌐 Abrir Dashboard Interactivo en Vivo</a></div>",
        "<h2 id='seccion-kpis'>1. Indicadores Clave (KPIs)</h2>",
        "<div class='kpis'>",
        f"<div class='kpi'><h4>Modelos</h4><p>{len(sel_archivos)} IFCs</p></div>",
        f"<div class='kpi'><h4>Elementos</h4><p>{total_el:,}</p></div>",
        f"<div class='kpi'><h4>Cumplimiento</h4><p>{pct_cumplimiento_global}%</p></div>",
        f"<div class='kpi'><h4>Naming BEP</h4><p>{pct_naming_ok}%</p></div>",
        f"<div class='kpi'><h4>Georref.</h4><p>{est_geo_txt}</p></div>",
        f"<div class='kpi'><h4>Peso Total</h4><p>{round(peso_total, 2)} MB</p></div>",
        "</div>",
        "<h2 id='seccion-matriz'>2. Matriz de Calidad por Modelo IFC</h2>",
        "<table><thead><tr><th>Archivo IFC</th><th>Dictamen</th>"
        "<th>Naming BEP</th><th>Elementos</th><th>Con Vacíos</th>"
        "<th>Proxies</th><th>% Cumplimiento</th></tr></thead>",
        f"<tbody>{filas_html_modelos}</tbody></table>",
        "<h2 id='seccion-bloques'>3. Cumplimiento por Bloques BEP</h2>",
        "<table><thead><tr><th>Bloque BEP</th><th>% Cumplimiento Medio</th>"
        f"</tr></thead><tbody>{filas_html_bloques}</tbody></table>",
        "<h2 id='seccion-criticos'>4. Top 25 Parámetros con Vacíos</h2>",
        "<table><thead><tr><th>Parámetro Oficial APV</th><th>Estado</th>"
        "<th>Con Dato</th><th>Comodín (-)</th><th>Vacíos</th>"
        f"<th>% Cumplimiento</th></tr></thead><tbody>{filas_html_top_vacios}"
        "</tbody></table></body></html>"
    ]
    html_ejecutivo = "\n".join(html_lineas)

    col_exp1, col_exp2, col_exp3 = st.columns(3)
    with col_exp1:
        st.download_button(
            label="📄 Descargar Informe Ejecutivo (HTML / Imprimible a PDF)",
            data=html_ejecutivo.encode("utf-8"),
            file_name="Informe_Ejecutivo_Auditoria_BIM_APV.html",
            mime="text/html",
            use_container_width=True
        )
    with col_exp2:
        csv_matriz = (
            grp_mod_exec[cols_matriz_exec].to_csv(index=False).encode("utf-8")
        )
        st.download_button(
            label="📊 Descargar Matriz Ejecutiva por Modelo (CSV / Excel)",
            data=csv_matriz,
            file_name="Matriz_Calidad_Modelos_APV.csv",
            mime="text/csv",
            use_container_width=True
        )
    with col_exp3:
        csv_vac_res = df_res_vacios.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Descargar Resumen de Parámetros APV (CSV / Excel)",
            data=csv_vac_res,
            file_name="Resumen_Parametros_BEP_APV.csv",
            mime="text/csv",
            use_container_width=True
        )

# --- PESTAÑA 13 ---
with tab13:
    st.subheader(
        "📈 13. Control de Avance Mensual y Regla de No-Regresión"
    )
    st.markdown(
        "**Regla de Negocio APV:** *El número de modelos IFC entregados "
        "jamás puede ser inferior al del mes anterior; siempre debe "
        "mantenerse igual o incrementarse conforme avanza la obra.*"
    )

    col_av1, col_av2, col_av3 = st.columns(3)
    diferencia_modelos = len(sel_archivos) - umbral_mes_anterior
    col_av1.metric("Modelos Entrega Mes Anterior (Base)", umbral_mes_anterior)
    col_av2.metric(
        "Modelos Entrega Actual",
        len(sel_archivos),
        delta=f"{diferencia_modelos:+d} modelos"
    )
    col_av3.metric(
        "Estado Regla de Avance",
        "✅ CUMPLE" if diferencia_modelos >= 0 else "🚨 INCUMPLE"
    )

    desglose_rev = []
    for arch in sel_archivos:
        partes = (
            str(arch)[:-4].split("_")
            if str(arch).lower().endswith(".ifc")
            else str(arch).split("_")
        )
        disc_arch = partes[4].upper() if len(partes) > 4 else "SIN_DISC"
        rev_arch = partes[6].upper() if len(partes) > 6 else "SIN_REV"
        desglose_rev.append({
            "Archivo IFC": arch,
            "Disciplina (Bloque 5)": disc_arch,
            "Revisión Actual (Bloque 7)": rev_arch,
            "Elementos Auditados": int(
                (df_original["Archivo_Origen"] == arch).sum()
            )
        })
    df_rev = pd.DataFrame(desglose_rev)

    c_rev1, c_rev2 = st.columns(2)
    with c_rev1:
        df_disc_cnt = (
            df_rev.groupby("Disciplina (Bloque 5)")
            .size()
            .reset_index(name="Cantidad Modelos")
        )
        fig_disc = px.bar(
            df_disc_cnt,
            x="Disciplina (Bloque 5)",
            y="Cantidad Modelos",
            text="Cantidad Modelos",
            title="Modelos IFC Entregados por Disciplina"
        )
        st.plotly_chart(fig_disc, use_container_width=True)
    with c_rev2:
        fig_revs = px.pie(
            df_rev,
            names="Revisión Actual (Bloque 7)",
            title="Distribución de Índices de Revisión (Bloque 7 BEP)",
            hole=0.4
        )
        st.plotly_chart(fig_revs, use_container_width=True)

    st.markdown(
        "#### 🔍 Comparador Opcional de Listado de Modelos vs Mes Anterior"
    )
    texto_modelos_mes_ant = st.text_area(
        "Pega aquí los nombres de los IFC del mes anterior (uno por línea):",
        placeholder="V_N035_OB_SEG_MOD_EaPavBtMC12_01D.ifc",
        height=120
    )
    if texto_modelos_mes_ant.strip():
        lista_ant = [
            x.strip()
            for x in texto_modelos_mes_ant.splitlines() if x.strip()
        ]

        def raiz_modelo(nombre):
            b = (
                str(nombre)[:-4]
                if str(nombre).lower().endswith(".ifc") else str(nombre)
            )
            p = b.split("_")
            return "_".join(p[:6]).upper() if len(p) >= 6 else b.upper()

        raices_ant = {raiz_modelo(x): x for x in lista_ant}
        raices_act = {raiz_modelo(x): x for x in sel_archivos}

        faltantes = [raices_ant[k] for k in raices_ant if k not in raices_act]
        nuevos = [raices_act[k] for k in raices_act if k not in raices_ant]

        if faltantes:
            st.error(
                f"🚨 **Faltan {len(faltantes)} modelos del mes anterior:** "
                f"{', '.join(faltantes)}"
            )
        else:
            st.success(
                "✅ Todos los modelos del listado anterior están presentes."
            )
        if nuevos:
            st.info(
                f"🆕 **Modelos nuevos incorporados ({len(nuevos)}):** "
                f"{', '.join(nuevos)}"
            )

# --- PESTAÑA 14 ---
with tab14:
    st.subheader(
        "🏗️ 14. Auditoría de Coherencia Cruzada 4D, 5D y 6D/GIS"
    )
    st.markdown(
        "Verifica que no existan incongruencias lógicas entre "
        "parámetros del mismo bloque (ej. elementos con **Medición** "
        "numérica pero sin **Unidad de Obra** o **Tipo de Medición**)."
    )

    reglas_coherencia = []

    cols_5d = [
        "02_04_01_APV_MEDICION",
        "02_05_01_APV_UNIDAD-OBRA",
        "02_06_01_APV_TIPO-MED"
    ]
    if all(c in df_original.columns for c in cols_5d):
        tiene_med = (
            (~mascara_vacio_rapida(df_original, "02_04_01_APV_MEDICION"))
            & (~mascara_comodin_rapida(df_original, "02_04_01_APV_MEDICION"))
        )
        falta_uo_o_tmed = (
            mascara_vacio_efectiva(df_original, "02_05_01_APV_UNIDAD-OBRA")
            | mascara_vacio_efectiva(df_original, "02_06_01_APV_TIPO-MED")
        )
        m_inco_5d = mask_arr & tiene_med & falta_uo_o_tmed
        reglas_coherencia.append(
            ("5D - Con Medición pero sin Unidad de Obra o Tipo-Med", m_inco_5d)
        )

    cols_4d = [
        "04_08_APV_PORCENTAJE-EJECUTADO",
        "04_01_APV_CÓDIGO-TAREA",
        "04_02_APV_NOMBRE-TAREA"
    ]
    if all(c in df_original.columns for c in cols_4d):
        tiene_pct = (
            (~mascara_vacio_rapida(df_original, "04_08_APV_PORCENTAJE-EJECUTADO"))
            & (~mascara_comodin_rapida(df_original, "04_08_APV_PORCENTAJE-EJECUTADO"))
        )
        falta_tarea = (
            mascara_vacio_efectiva(df_original, "04_01_APV_CÓDIGO-TAREA")
            | mascara_vacio_efectiva(df_original, "04_02_APV_NOMBRE-TAREA")
        )
        m_inco_4d = mask_arr & tiene_pct & falta_tarea
        reglas_coherencia.append(
            ("4D - Con % Ejecutado pero sin Código/Nombre de Tarea", m_inco_4d)
        )

    cols_6d = [
        "08_01_APV_PLAN-MANTENIMIENTO",
        "08_03_APV_COD-MANTENIMIENTO"
    ]
    if all(c in df_original.columns for c in cols_6d):
        tiene_plan = (
            (~mascara_vacio_rapida(df_original, "08_01_APV_PLAN-MANTENIMIENTO"))
            & (~mascara_comodin_rapida(df_original, "08_01_APV_PLAN-MANTENIMIENTO"))
        )
        falta_cod_mant = mascara_vacio_efectiva(
            df_original, "08_03_APV_COD-MANTENIMIENTO"
        )
        m_inco_6d = mask_arr & tiene_plan & falta_cod_mant
        reglas_coherencia.append(
            ("6D - Con Plan de Mantenimiento pero sin Código", m_inco_6d)
        )

    res_coherencia = [
        {
            "Regla de Coherencia BEP": nombre_r,
            "Elementos Incoherentes": int(m_r.sum()),
            "Estado": (
                "✅ OK" if int(m_r.sum()) == 0
                else f"⚠️ Revisar ({int(m_r.sum()):,})"
            )
        }
        for nombre_r, m_r in reglas_coherencia
    ]
    st.dataframe(
        pd.DataFrame(res_coherencia),
        use_container_width=True,
        hide_index=True
    )

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
                    "02_04_01_APV_MEDICION", "02_05_01_APV_UNIDAD-OBRA",
                    "02_06_01_APV_TIPO-MED", "04_01_APV_CÓDIGO-TAREA",
                    "04_02_APV_NOMBRE-TAREA", "04_08_APV_PORCENTAJE-EJECUTADO"
                ] if c in df_original.columns
            ]
            st.dataframe(
                df_original[cols_14].iloc[idx_14[:5000]],
                use_container_width=True
            )
        else:
            st.success(
                "✅ Cero incoherencias en esta regla para los modelos seleccionados."
            )

# --- PESTAÑA 15 ---
with tab15:
    st.subheader(
        "📥 15. Exportación de Cuadro de Control de Entregables (XLSX) & Discernimiento de Software"
    )
    st.markdown(
        "Genera y exporta un archivo en formato **XLSX** estructurado de forma idéntica a tu cuadro de control "
        "de entregables de la APV. El motor **discierne automáticamente la tipología, el bloque de disciplina y "
        "si el IFC proviene de Autodesk Revit o de Autodesk Civil 3D** analizando las clases semánticas."
    )

    # Construir el DataFrame de control de entregables tipo cuadro APV
    filas_export_excel = []
    for arch in archivos_disp:
        sub_m = df_original.loc[df_original["Archivo_Origen"] == arch]
        n_elem_mod = len(sub_m)
        tipo_mod = discernir_tipo_modelo(arch, sub_m)
        software_orig = discernir_software_origen(sub_m)
        diag_bep = diagnosticar_nombre_bep(arch)
        cumple_naming = "SÍ" if "✅" in diag_bep else "NO"
        
        # Calcular cumplimiento específico del modelo
        if n_elem_mod > 0 and arch in matriz_presencia_nw.index:
            s_p_mod = pres_all_arr[df_original["Archivo_Origen"] == arch].sum()
            s_v_mod = vac_nw_all_arr[df_original["Archivo_Origen"] == arch].sum()
            denom_m = max(1, s_p_mod + s_v_mod)
            pct_mod = round((s_p_mod / denom_m) * 100, 1)
        else:
            pct_mod = 0.0

        estado_aprobacion = "APROBADO" if pct_mod >= 95 and cumple_naming == "SÍ" else "REVISAR / SUBSANAR"

        filas_export_excel.append({
            "Archivo IFC": arch,
            "Tipo de Modelo / Disciplina": tipo_mod,
            "Software de Autoría Origen": software_orig,
            "Elementos BIM": n_elem_mod,
            "Cumple Naming BEP": cumple_naming,
            "% Cumplimiento Parámetros APV": f"{pct_mod}%",
            "Estado Control APV": estado_aprobacion
        })

    df_cuadro_apv = pd.DataFrame(filas_export_excel)
    st.dataframe(df_cuadro_apv, use_container_width=True, hide_index=True)

    # Función para generar archivo Excel en memoria con estilo
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_cuadro_apv.to_excel(writer, sheet_name="Cuadro_Control_APV", index=False)
        workbook = writer.book
        worksheet = writer.sheets["Cuadro_Control_APV"]
        
        # Formatos para Excel
        header_format = workbook.add_format({
            "bold": True,
            "font_color": "white",
            "bg_color": "#0f172a",
            "align": "center",
            "valign": "middle",
            "border": 1
        })
        cell_format = workbook.add_format({
            "align": "left",
            "valign": "middle",
            "border": 1
        })
        center_format = workbook.add_format({
            "align": "center",
            "valign": "middle",
            "border": 1
        })
        
        # Aplicar formato a cabeceras
        for col_num, value in enumerate(df_cuadro_apv.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # Ajustar anchos de columnas
        for i, col in enumerate(df_cuadro_apv.columns):
            max_len = max(df_cuadro_apv[col].astype(str).map(len).max(), len(col)) + 4
            worksheet.set_column(i, i, max_len)

    excel_data = output.getvalue()

    st.download_button(
        label="📥 Descargar Cuadro de Control de Entregables (XLSX - Formato Oficial APV)",
        data=excel_data,
        file_name="Cuadro_Control_Entregables_APV_Auditado.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

print("[DIAG FIN] Dashboard de 15 pestañas renderizado con éxito", flush=True)