"""Diccionario de datos generado desde el propio dataset.

Tipo, porcentaje de nulos y cardinalidad se derivan de la capa curated en
cada ejecución; el único campo manual — y el único con valor documental —
es la descripción. Si aparece una columna nueva, la siguiente ejecución la
registra automáticamente con descripción ``PENDIENTE``, señalando
documentación faltante. La documentación deja de ser una tarea del final:
es una salida más del pipeline.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import ruta

#: Descripciones de negocio de la capa curated (el único insumo manual).
DESCRIPCIONES: dict[str, str] = {
    "venta_id": "Número de tiquete del POS; identificador único (llave primaria).",
    "fecha": "Fecha de la venta, dentro de la ventana de análisis.",
    "cliente_id": "Cliente del programa Aroma+; verificado contra stg_clientes (FK).",
    "producto_id": "Código del producto; verificado contra el catálogo.",
    "producto": "Nombre comercial del producto (del catálogo).",
    "categoria": "Categoría del producto (del catálogo).",
    "sede": "Barra del punto piloto donde se registró la venta (Centro o Norte).",
    "cantidad": "Unidades vendidas; siempre mayor que cero tras la validación.",
    "precio_unitario": "Precio de venta por unidad, en COP (del catálogo).",
    "costo_unitario": "Costo por unidad, en COP (del catálogo).",
    "ingreso": "Variable derivada: cantidad × precio_unitario.",
    "margen": "Variable derivada: ingreso − cantidad × costo_unitario.",
}


def construir_diccionario(df: pd.DataFrame, descripciones: dict[str, str] | None = None) -> pd.DataFrame:
    """Deriva el diccionario de datos de un DataFrame.

    Args:
        df: Tabla a documentar (normalmente la capa curated).
        descripciones: Descripciones de negocio por columna. Toda columna
            sin descripción queda registrada como ``PENDIENTE``.

    Returns:
        Un DataFrame con una fila por columna: nombre, tipo, % de nulos,
        cardinalidad y descripción.
    """
    desc = DESCRIPCIONES if descripciones is None else descripciones
    filas = [
        {
            "columna": col,
            "tipo": str(df[col].dtype),
            "nulos_pct": round(float(df[col].isna().mean()) * 100, 1),
            "unicos": int(df[col].nunique()),
            "descripcion": desc.get(col, "PENDIENTE"),
        }
        for col in df.columns
    ]
    return pd.DataFrame(filas)


def escribir_diccionario(df: pd.DataFrame, cfg: dict[str, Any]) -> str:
    """Genera ``docs/data_dictionary.md`` a partir de la capa curated.

    Returns:
        Ruta (relativa) del archivo escrito.
    """
    docs = ruta(cfg, "docs")
    docs.mkdir(parents=True, exist_ok=True)
    dic = construir_diccionario(df)
    lineas = [
        "# Diccionario de datos · capa curated",
        "",
        "Archivo **generado por el pipeline** en cada ejecución "
        "(`python -m src.pipeline`). No se edita a mano: la única fuente "
        "manual son las descripciones en `src/dictionary.py`.",
        "",
        "| columna | tipo | nulos % | únicos | descripción |",
        "|---|---|---:|---:|---|",
    ]
    for _, r in dic.iterrows():
        lineas.append(
            f"| `{r['columna']}` | `{r['tipo']}` | {r['nulos_pct']} | {r['unicos']} | {r['descripcion']} |"
        )
    destino = docs / "data_dictionary.md"
    destino.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    return str(destino)
