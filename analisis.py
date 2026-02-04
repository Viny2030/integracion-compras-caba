import pandas as pd
import numpy as np
import re

# =====================================================
# 1. REGLAS HEURÍSTICAS DE RIESGO (SIMPLIFICADAS)
# =====================================================
PALABRAS_RIESGO_ALTO = [
    "contratación directa",
    "emergencia",
    "excepción",
    "urgente",
    "ampliación",
    "redeterminación",
]

PALABRAS_RIESGO_MEDIO = [
    "licitación privada",
    "adjudicación",
    "prórroga",
    "renovación",
]

# =====================================================
# 2. FUNCIÓN PRINCIPAL DE ANÁLISIS
# =====================================================
def analizar_boletin(df: pd.DataFrame):
    """
    Analiza compras y obras CABA y genera indicadores de riesgo.
    Devuelve:
    - df_analizado
    - resumen (dict)
    - reglas_activadas (list)
    """

    df = df.copy()

    # -------------------------------------------------
    # BLINDAJE DE COLUMNAS MÍNIMAS
    # -------------------------------------------------
    columnas_minimas = [
        "fecha",
        "seccion",
        "detalle",
        "tipo_decision",
        "origen",
        "link",
        "transferencia",
    ]

    for col in columnas_minimas:
        if col not in df.columns:
            df[col] = ""

    # -------------------------------------------------
    # NORMALIZACIÓN DE TEXTO
    # -------------------------------------------------
    df["detalle"] = (
        df["detalle"]
        .astype(str)
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
    )

    # -------------------------------------------------
    # LIMPIEZA DE MONTO / TRANSFERENCIA
    # -------------------------------------------------
    df["transferencia"] = (
        df["transferencia"]
        .astype(str)
        .str.replace(r"[^0-9.,-]", "", regex=True)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )

    df["transferencia"] = pd.to_numeric(
        df["transferencia"], errors="coerce"
    ).fillna(0.0)

    # -------------------------------------------------
    # 3. DETECCIÓN DE REGLAS DE RIESGO
    # -------------------------------------------------
    reglas_detectadas = []

    def evaluar_reglas(texto):
        reglas = []

        for p in PALABRAS_RIESGO_ALTO:
            if p in texto:
                reglas.append(f"Riesgo Alto: '{p}'")

        for p in PALABRAS_RIESGO_MEDIO:
            if p in texto:
                reglas.append(f"Riesgo Medio: '{p}'")

        return reglas

    df["reglas_activadas"] = df["detalle"].apply(evaluar_reglas)

    # -------------------------------------------------
    # 4. ÍNDICE DE FENÓMENO CORRUPTIVO (IFC)
    # -------------------------------------------------
    def calcular_ifc(fila):
        score = 0.0

        # Peso por monto
        if fila["transferencia"] > 100_000_000:
            score += 4
        elif fila["transferencia"] > 20_000_000:
            score += 2
        elif fila["transferencia"] > 5_000_000:
            score += 1

        # Peso por reglas
        for r in fila["reglas_activadas"]:
            if "Riesgo Alto" in r:
                score += 3
            elif "Riesgo Medio" in r:
                score += 1.5

        return round(score, 2)

    df["indice_fenomeno_corruptivo"] = df.apply(calcular_ifc, axis=1)

    # -------------------------------------------------
    # 5. CLASIFICACIÓN DE RIESGO
    # -------------------------------------------------
    def clasificar_riesgo(ifc):
        if ifc >= 6:
            return "Alto"
        elif ifc >= 3:
            return "Medio"
        else:
            return "Bajo"

    df["nivel_riesgo_teorico"] = df["indice_fenomeno_corruptivo"].apply(
        clasificar_riesgo
    )

    # -------------------------------------------------
    # 6. ESCENARIO (NO OBLIGATORIO)
    # -------------------------------------------------
    if "escenario_monteverde" not in df.columns:
        df["escenario_monteverde"] = "No definido"

    # -------------------------------------------------
    # 7. RESUMEN EJECUTIVO
    # -------------------------------------------------
    resumen = {
        "total_registros": len(df),
        "riesgo_alto": int((df["nivel_riesgo_teorico"] == "Alto").sum()),
        "riesgo_medio": int((df["nivel_riesgo_teorico"] == "Medio").sum()),
        "riesgo_bajo": int((df["nivel_riesgo_teorico"] == "Bajo").sum()),
        "monto_total": float(df["transferencia"].sum()),
        "ifc_promedio": float(df["indice_fenomeno_corruptivo"].mean()),
    }

    reglas_activadas = (
        df["reglas_activadas"]
        .explode()
        .dropna()
        .unique()
        .tolist()
    )

    return df, resumen, reglas_activadas
