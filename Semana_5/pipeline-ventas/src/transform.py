"""Paso 2 del pipeline: transformación e integración.

Dos responsabilidades, en este orden:

1. **Staging** — tipar y normalizar cada fuente por separado
   (``stg_ventas``, ``stg_clientes``, ``stg_productos``), persistidas en
   ``data/staging`` como Parquet.
2. **Integración** — construir ``ventas_enriq``: la tabla de ventas unida
   con el catálogo de productos, con las variables derivadas ``ingreso``
   y ``margen``.

Toda la lógica es funcional: cada función recibe DataFrames y devuelve
DataFrames nuevos, sin estado global ni efectos ocultos.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from .config import ruta


def _staging_ventas(df: pd.DataFrame) -> pd.DataFrame:
    """Tipa la tabla de ventas y elimina duplicados exactos."""
    out = df.copy()
    out["fecha"] = pd.to_datetime(out["fecha"], format="%Y-%m-%d")
    out["cantidad"] = pd.to_numeric(out["cantidad"], errors="raise").astype("int64")
    for col in ("venta_id", "cliente_id", "producto_id", "sede"):
        out[col] = out[col].astype("string").str.strip()
    return out.drop_duplicates()


def _staging_clientes(df: pd.DataFrame) -> pd.DataFrame:
    """Normaliza identificadores y texto de la tabla de clientes."""
    out = df.copy()
    for col in out.columns:
        out[col] = out[col].astype("string").str.strip()
    return out.drop_duplicates(subset="cliente_id")


def _staging_productos(df: pd.DataFrame) -> pd.DataFrame:
    """Tipa el catálogo de productos y verifica precios positivos."""
    out = df.copy()
    out["precio_unitario"] = pd.to_numeric(out["precio_unitario"]).astype("int64")
    out["costo_unitario"] = pd.to_numeric(out["costo_unitario"]).astype("int64")
    for col in ("producto_id", "nombre", "categoria"):
        out[col] = out[col].astype("string").str.strip()
    return out.drop_duplicates(subset="producto_id")


def transform(crudo: dict[str, pd.DataFrame], cfg: dict[str, Any]) -> pd.DataFrame:
    """Construye el staging, lo persiste y devuelve la tabla integrada.

    Args:
        crudo: Salida de :func:`src.extract.extract`.
        cfg: Configuración del proyecto.

    Returns:
        ``ventas_enriq``: una fila por venta, con producto, categoría,
        precio, costo y las variables derivadas ``ingreso`` y ``margen``.
    """
    stg = ruta(cfg, "staging")
    stg.mkdir(parents=True, exist_ok=True)

    stg_ventas = _staging_ventas(crudo["ventas"])
    stg_clientes = _staging_clientes(crudo["clientes"])
    stg_productos = _staging_productos(crudo["productos"])

    stg_ventas.to_parquet(stg / "stg_ventas.parquet", index=False)
    stg_clientes.to_parquet(stg / "stg_clientes.parquet", index=False)
    stg_productos.to_parquet(stg / "stg_productos.parquet", index=False)

    # Integración: join con el catálogo y variables derivadas.
    enriq = stg_ventas.merge(
        stg_productos[["producto_id", "nombre", "categoria", "precio_unitario", "costo_unitario"]],
        on="producto_id",
        how="left",
        validate="many_to_one",
    ).rename(columns={"nombre": "producto"})
    enriq["ingreso"] = enriq["cantidad"] * enriq["precio_unitario"]
    enriq["margen"] = enriq["ingreso"] - enriq["cantidad"] * enriq["costo_unitario"]
    return enriq
