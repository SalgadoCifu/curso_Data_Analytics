"""Paso 1 del pipeline: extracción.

``extract()`` lee las tres fuentes de la capa raw y las devuelve como
DataFrames sin transformar. La capa raw es inmutable: este paso **nunca**
escribe sobre ella; si una fuente no existe, el paso falla de forma
explícita en lugar de continuar con datos parciales.
"""

from __future__ import annotations

import json
import re
from typing import Any

import pandas as pd

from .config import ruta


def _parsear_tabla_html(html: str) -> pd.DataFrame:
    """Extrae la tabla de clientes de la página HTML capturada.

    Se usa un analizador propio basado en expresiones regulares para no
    añadir dependencias; el HTML de la fuente es estable y controlado.
    """
    encabezados = re.findall(r"<th>(.*?)</th>", html)
    filas = [re.findall(r"<td>(.*?)</td>", tr) for tr in re.findall(r"<tr>(.*?)</tr>", html, flags=re.S)]
    filas = [f for f in filas if f]  # descarta la fila de encabezados (sin <td>)
    return pd.DataFrame(filas, columns=encabezados)


def extract(cfg: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Lee las fuentes crudas y las devuelve tal cual llegaron.

    Args:
        cfg: Configuración del proyecto.

    Returns:
        Diccionario con los DataFrames ``ventas``, ``clientes`` y
        ``productos``, fieles a la fuente (sin tipar ni limpiar).

    Raises:
        FileNotFoundError: si falta alguna de las fuentes en ``data/raw``.
    """
    raw = ruta(cfg, "raw")
    rutas = {
        "ventas": raw / "ventas_api.json",
        "clientes": raw / "clientes.html",
        "productos": raw / "productos.csv",
    }
    faltantes = [str(p) for p in rutas.values() if not p.exists()]
    if faltantes:
        raise FileNotFoundError(
            "Fuentes ausentes en la capa raw: " + ", ".join(faltantes)
            + ". Ejecutar `python -m src.pipeline --regenerar-fuentes`."
        )

    carga = json.loads(rutas["ventas"].read_text(encoding="utf-8"))
    ventas = pd.DataFrame(carga["data"])
    clientes = _parsear_tabla_html(rutas["clientes"].read_text(encoding="utf-8"))
    productos = pd.read_csv(rutas["productos"])
    return {"ventas": ventas, "clientes": clientes, "productos": productos}
