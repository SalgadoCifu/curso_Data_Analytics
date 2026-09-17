"""Paso 3 del pipeline: validación con acción declarada.

Cinco reglas corren en cada ejecución. Cada una declara de antemano su
umbral y su acción cuando falla — nada queda a criterio del momento:

===========  =============================================  ===========
Regla        Qué verifica                                   Acción
===========  =============================================  ===========
esquema      Columnas esperadas con el tipo correcto        DETENER
unicidad     ``venta_id`` sin duplicados                    DETENER
no_nulos     Campos críticos completos (umbral 0 %)         CUARENTENA
rangos       ``cantidad > 0``, fecha en ventana, FK cliente CUARENTENA
frescura     máx(fecha) dentro del umbral respecto al corte ADVERTIR
===========  =============================================  ===========

* **DETENER** lanza :class:`ErrorDeValidacion`: el defecto invalida el
  análisis y ningún dato llega a la capa curated.
* **CUARENTENA** aísla las filas que incumplen la regla en
  ``data/quarantine`` (con la regla que las rechazó), las contabiliza y
  deja continuar el resto.
* **ADVERTIR** registra el hallazgo en el reporte y la ejecución continúa.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import ruta

#: Esquema esperado de ``ventas_enriq``: columna → prefijo del dtype.
ESQUEMA_ESPERADO: dict[str, str] = {
    "venta_id": "str",
    "fecha": "datetime64",
    "cliente_id": "str",
    "producto_id": "str",
    "producto": "str",
    "categoria": "str",
    "sede": "str",
    "cantidad": "int",
    "precio_unitario": "int",
    "costo_unitario": "int",
    "ingreso": "int",
    "margen": "int",
}

#: Campos que no admiten nulos (umbral definido en ``config.yaml``).
CAMPOS_CRITICOS = ["venta_id", "fecha", "cliente_id", "producto_id", "cantidad", "sede"]


class ErrorDeValidacion(RuntimeError):
    """Defecto de datos que invalida el análisis: el pipeline se detiene."""


def _verificar_esquema(df: pd.DataFrame) -> list[str]:
    """Devuelve la lista de problemas de esquema (vacía si no hay)."""
    problemas: list[str] = []
    for col, prefijo in ESQUEMA_ESPERADO.items():
        if col not in df.columns:
            problemas.append(f"falta la columna '{col}'")
        elif not str(df[col].dtype).startswith(prefijo):
            problemas.append(f"'{col}' tiene dtype {df[col].dtype}, se esperaba {prefijo}*")
    return problemas


def validate(df: pd.DataFrame, cfg: dict[str, Any]) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Aplica las cinco reglas y devuelve los datos válidos y el reporte.

    Args:
        df: Tabla integrada ``ventas_enriq`` producida por ``transform``.
        cfg: Configuración del proyecto.

    Returns:
        Tupla ``(df_valido, reporte)``. El reporte incluye, por regla, el
        resultado y el número de filas afectadas, más las advertencias.

    Raises:
        ErrorDeValidacion: si falla una regla con acción DETENER.
    """
    reporte: dict[str, Any] = {"reglas": {}, "advertencias": [], "filas_entrada": len(df)}
    corte = pd.Timestamp(cfg["parametros"]["fecha_corte"])
    ventana = cfg["parametros"]["dias_ventana"]
    umbral_frescura = cfg["umbrales"]["frescura_dias"]
    umbral_nulos = cfg["umbrales"]["nulos_criticos_pct"]

    # 1 · esquema — DETENER ------------------------------------------------
    problemas = _verificar_esquema(df)
    reporte["reglas"]["esquema"] = {"accion": "detener", "problemas": problemas}
    if problemas:
        raise ErrorDeValidacion("Esquema inválido: " + "; ".join(problemas))

    # 2 · unicidad — DETENER ----------------------------------------------
    duplicados = int(df["venta_id"].duplicated().sum())
    reporte["reglas"]["unicidad"] = {"accion": "detener", "duplicados": duplicados}
    if duplicados:
        raise ErrorDeValidacion(
            f"Unicidad violada: {duplicados} venta_id duplicados. "
            "Un identificador repetido implica doble conteo de ingresos."
        )

    # 3 · no_nulos — CUARENTENA -------------------------------------------
    mascara_nulos = df[CAMPOS_CRITICOS].isna().any(axis=1)
    pct_nulos = 100 * mascara_nulos.mean()
    en_cuarentena = df[mascara_nulos].assign(regla="no_nulos") if pct_nulos > umbral_nulos else df.iloc[0:0].assign(regla="no_nulos")
    reporte["reglas"]["no_nulos"] = {"accion": "cuarentena", "filas": int(mascara_nulos.sum())}

    # 4 · rangos — CUARENTENA ----------------------------------------------
    clientes = pd.read_parquet(ruta(cfg, "staging") / "stg_clientes.parquet")
    fk_ok = df["cliente_id"].isin(set(clientes["cliente_id"]))
    en_ventana = df["fecha"].between(corte - pd.Timedelta(days=ventana), corte)
    mascara_rangos = ~((df["cantidad"] > 0) & en_ventana & fk_ok) & ~mascara_nulos
    cuarentena_rangos = df[mascara_rangos].assign(regla="rangos")
    reporte["reglas"]["rangos"] = {"accion": "cuarentena", "filas": int(mascara_rangos.sum())}

    # 5 · frescura — ADVERTIR ----------------------------------------------
    antiguedad = int((corte - df["fecha"].max()).days)
    reporte["reglas"]["frescura"] = {"accion": "advertir", "antiguedad_dias": antiguedad}
    if antiguedad > umbral_frescura:
        reporte["advertencias"].append(
            f"Frescura: los datos tienen {antiguedad} días y el umbral es {umbral_frescura}. "
            "La ejecución continúa con la advertencia registrada."
        )

    # ── Persistir la cuarentena y separar los datos válidos ───────────────
    qdir = ruta(cfg, "quarantine")
    qdir.mkdir(parents=True, exist_ok=True)
    cuarentena = pd.concat([en_cuarentena, cuarentena_rangos], ignore_index=True)
    cuarentena.to_csv(qdir / "ventas_rechazadas.csv", index=False)
    reporte["filas_cuarentena"] = len(cuarentena)

    valido = df[~(mascara_nulos | mascara_rangos)].copy()
    reporte["filas_validas"] = len(valido)
    return valido, reporte
