"""Paso 4 del pipeline: carga idempotente y verificación por hash.

``load()`` escribe la capa curated en tres formatos coherentes entre sí
— Parquet, CSV y una tabla SQLite — y calcula un hash SHA-256 sobre una
representación canónica de los datos. La carga es **idempotente**:
ejecutar el pipeline N veces deja el sistema exactamente igual que
ejecutarlo una vez (``if_exists="replace"``, nunca ``append``).

El hash es el criterio de verificación de reproducibilidad: dos
ejecuciones consecutivas deben producir el mismo valor.
"""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Any

import pandas as pd

from .config import ROOT, ruta

#: Orden canónico de columnas de la capa curated.
COLUMNAS_CURATED = [
    "venta_id", "fecha", "cliente_id", "producto_id", "producto", "categoria",
    "sede", "cantidad", "precio_unitario", "costo_unitario", "ingreso", "margen",
]


def hash_canonico(df: pd.DataFrame) -> str:
    """Calcula el SHA-256 de una representación canónica del DataFrame.

    El hash funciona como la huella digital de la tabla: si dos tablas
    producen la misma huella, su contenido es idéntico. La canonicalización
    (orden fijo de filas y columnas, fechas en ISO, CSV sin índice)
    garantiza que la huella dependa solo del contenido de los datos y no
    de cómo estén escritos u ordenados.
    """
    canon = df[COLUMNAS_CURATED].sort_values("venta_id").reset_index(drop=True).copy()
    canon["fecha"] = canon["fecha"].dt.strftime("%Y-%m-%d")
    return hashlib.sha256(canon.to_csv(index=False).encode("utf-8")).hexdigest()


def load(df: pd.DataFrame, cfg: dict[str, Any]) -> dict[str, Any]:
    """Escribe la capa curated de forma idempotente y devuelve el resumen.

    Args:
        df: Datos validados por :func:`src.validate.validate`.
        cfg: Configuración del proyecto.

    Returns:
        Resumen de la ejecución: filas, ingreso y margen totales, hash y
        rutas de los artefactos escritos.
    """
    cur = ruta(cfg, "curated")
    cur.mkdir(parents=True, exist_ok=True)
    curated = df[COLUMNAS_CURATED].sort_values("venta_id").reset_index(drop=True)

    curated.to_parquet(cur / "ventas.parquet", index=False)
    curated.to_csv(cur / "ventas.csv", index=False)
    with sqlite3.connect(ruta(cfg, "db")) as con:
        curated.to_sql("ventas", con, if_exists="replace", index=False)  # idempotente

    digest = hash_canonico(curated)
    (cur / "hash.txt").write_text(digest + "\n", encoding="utf-8")

    return {
        "filas": len(curated),
        "ingreso_total": int(curated["ingreso"].sum()),
        "margen_total": int(curated["margen"].sum()),
        "hash": digest,
        "artefactos": [str(p.relative_to(ROOT)) for p in (cur / "ventas.parquet", cur / "ventas.csv", ruta(cfg, "db"))],
    }
