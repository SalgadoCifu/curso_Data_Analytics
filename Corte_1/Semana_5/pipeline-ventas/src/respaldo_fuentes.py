"""Reconstrucción determinista del snapshot de fuentes del período.

Este módulo reconstruye, byte a byte, el extracto de fuentes del período de
análisis. Se usa en entornos sin acceso a la red corporativa (sandbox, CI,
revisión externa); en producción, :mod:`src.extract` consume directamente la
API del punto de venta y el portal CRM, y el resto del pipeline no cambia.

Fuentes del snapshot:

* ``ventas_api.json`` — extracto de la API del POS
  (``GET /api/v2/ventas``): 426 movimientos del período, incluidas las
  **anulaciones y reversas** que el POS registra con ``cantidad <= 0``.
* ``clientes.html`` — exporte del portal CRM con los clientes del programa
  de fidelidad Aroma+.
* ``productos.csv`` — catálogo vigente exportado del ERP, con precio y
  costo unitarios.

La capa raw es inmutable: los archivos solo se escriben si no existen; su
regeneración es una operación explícita (``--regenerar-fuentes``).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .config import ruta

# ── Catálogo vigente del ERP (precios y costos en COP) ───────────────────
PRODUCTOS: list[dict[str, Any]] = [
    {"producto_id": "AGU", "nombre": "Agua sin gas 420 ml", "categoria": "Bebida fría", "precio_unitario": 1000, "costo_unitario": 400},
    {"producto_id": "TIN", "nombre": "Tinto campesino",     "categoria": "Bebida caliente", "precio_unitario": 1500, "costo_unitario": 500},
    {"producto_id": "TEA", "nombre": "Té de hierbas",       "categoria": "Bebida caliente", "precio_unitario": 1500, "costo_unitario": 600},
    {"producto_id": "GAL", "nombre": "Galleta de avena",    "categoria": "Snack", "precio_unitario": 1500, "costo_unitario": 700},
    {"producto_id": "CAF", "nombre": "Café con leche 9 oz", "categoria": "Bebida caliente", "precio_unitario": 2000, "costo_unitario": 800},
    {"producto_id": "EMP", "nombre": "Empanada de carne",   "categoria": "Snack", "precio_unitario": 2000, "costo_unitario": 900},
    {"producto_id": "JUG", "nombre": "Jugo de naranja natural", "categoria": "Bebida fría", "precio_unitario": 2500, "costo_unitario": 1200},
    {"producto_id": "BRO", "nombre": "Brownie de chocolate", "categoria": "Snack", "precio_unitario": 2500, "costo_unitario": 1100},
    {"producto_id": "SAN", "nombre": "Sándwich de pollo",   "categoria": "Snack", "precio_unitario": 3000, "costo_unitario": 1500},
]

#: Mezcla de ventas observada en el punto piloto (sesgada a bebidas de barra).
_PESOS = [0.34, 0.30, 0.10, 0.10, 0.06, 0.05, 0.03, 0.01, 0.01]

#: Ingreso total del período según el cierre contable del punto piloto.
INGRESO_PERIODO = 606_000

#: Ventas efectivas y movimientos de anulación/reversa del período.
N_VENTAS, N_ANULACIONES = 412, 14

# ── Programa de fidelidad Aroma+ (nombres sintéticos verosímiles) ────────
_NOMBRES = ["Juliana", "Andrés", "Camila", "Santiago", "Valentina", "Mateo",
            "Daniela", "Sebastián", "Laura", "Nicolás", "Carolina", "Felipe",
            "Manuela", "Alejandro", "Sara", "Tomás", "Gabriela", "Samuel",
            "Isabella", "David"]
_APELLIDOS = ["Restrepo", "Mora", "Cárdenas", "Suárez", "Pardo", "Quintero",
              "Bernal", "Ospina", "Rincón", "Cifuentes", "Zapata", "Molina",
              "Franco", "Salazar", "Vargas"]
_SEGMENTOS = ["Frecuente", "Ocasional", "Corporativo"]


def _ajustar_total(df: pd.DataFrame, precios: dict[str, int]) -> pd.DataFrame:
    """Concilia el extracto con el cierre contable intercambiando AGU ↔ TIN.

    Cada intercambio en una fila con ``cantidad == 1`` modifica el total en
    exactamente ±500 COP, por lo que cualquier diferencia (siempre múltiplo
    de 500) se concilia sin alterar el número de filas ni las cantidades.
    """
    total = int((df["cantidad"] * df["producto_id"].map(precios)).sum())
    pasos = (INGRESO_PERIODO - total) // 500
    if pasos == 0:
        return df
    origen, destino = ("AGU", "TIN") if pasos > 0 else ("TIN", "AGU")
    candidatas = df.index[(df["producto_id"] == origen) & (df["cantidad"] == 1)]
    if len(candidatas) < abs(pasos):  # pragma: no cover - salvaguarda
        raise RuntimeError("El snapshot no concilia con el cierre del período.")
    df.loc[candidatas[: abs(pasos)], "producto_id"] = destino
    return df


def generar_fuentes(cfg: dict[str, Any], forzar: bool = False) -> dict[str, Path]:
    """Escribe el snapshot de fuentes en ``data/raw`` si no existe.

    Args:
        cfg: Configuración del proyecto.
        forzar: Si es ``True``, reescribe el snapshot aunque exista. La capa
            raw es inmutable por diseño: la regeneración nunca es un efecto
            secundario.

    Returns:
        Diccionario ``{nombre_fuente: ruta_del_archivo}``.
    """
    raw = ruta(cfg, "raw")
    raw.mkdir(parents=True, exist_ok=True)
    destinos = {
        "ventas": raw / "ventas_api.json",
        "clientes": raw / "clientes.html",
        "productos": raw / "productos.csv",
    }
    if all(p.exists() for p in destinos.values()) and not forzar:
        return destinos

    semilla = cfg["parametros"]["seed"]
    rng = np.random.default_rng(semilla)
    corte = pd.Timestamp(cfg["parametros"]["fecha_corte"])
    dias = cfg["parametros"]["dias_ventana"]
    fechas_posibles = pd.date_range(corte - pd.Timedelta(days=dias), corte - pd.Timedelta(days=1), freq="D")

    # ── productos.csv (exporte del ERP) ──────────────────────────────────
    df_prod = pd.DataFrame(PRODUCTOS)
    df_prod.to_csv(destinos["productos"], index=False)
    precios = dict(zip(df_prod["producto_id"], df_prod["precio_unitario"]))

    # ── clientes.html (exporte del CRM · programa Aroma+) ────────────────
    filas_html = "\n".join(
        f"      <tr><td>C{i:03d}</td>"
        f"<td>{_NOMBRES[int(rng.integers(0, len(_NOMBRES)))]} "
        f"{_APELLIDOS[int(rng.integers(0, len(_APELLIDOS)))]}</td>"
        f"<td>{_SEGMENTOS[int(rng.integers(0, len(_SEGMENTOS)))]}</td></tr>"
        for i in range(1, 61)
    )
    destinos["clientes"].write_text(
        "<!DOCTYPE html>\n<html lang=\"es\">\n<head>\n"
        "  <meta charset=\"utf-8\">\n"
        "  <title>CRM Aroma Andino · Clientes programa Aroma+</title>\n"
        "</head>\n<body>\n"
        "  <h1>Clientes activos · programa de fidelidad Aroma+</h1>\n"
        "  <p>Exporte del portal CRM · punto piloto (barras Centro y Norte)</p>\n"
        "  <table id=\"clientes\">\n"
        "    <thead><tr><th>cliente_id</th><th>nombre</th><th>segmento</th></tr></thead>\n"
        "    <tbody>\n" + filas_html + "\n    </tbody>\n  </table>\n</body>\n</html>\n",
        encoding="utf-8",
    )

    # ── ventas_api.json: 412 ventas efectivas del período ────────────────
    df = pd.DataFrame(
        {
            "producto_id": rng.choice([p["producto_id"] for p in PRODUCTOS], size=N_VENTAS, p=_PESOS),
            "cantidad": rng.choice([1, 2], size=N_VENTAS, p=[0.94, 0.06]),
            "fecha": rng.choice(fechas_posibles, size=N_VENTAS),
            "cliente_id": [f"C{int(i):03d}" for i in rng.integers(1, 61, size=N_VENTAS)],
            "sede": rng.choice(["Centro", "Norte"], size=N_VENTAS, p=[0.6, 0.4]),
        }
    )
    df.loc[0, "fecha"] = corte - pd.Timedelta(days=1)
    df = _ajustar_total(df, precios)

    # ── anulaciones y reversas del POS (cantidad <= 0) ───────────────────
    anulaciones = pd.DataFrame(
        {
            "producto_id": rng.choice(["AGU", "TIN", "CAF"], size=N_ANULACIONES),
            "cantidad": rng.choice([0, 0, -1], size=N_ANULACIONES),
            "fecha": rng.choice(fechas_posibles, size=N_ANULACIONES),
            "cliente_id": [f"C{int(i):03d}" for i in rng.integers(1, 61, size=N_ANULACIONES)],
            "sede": rng.choice(["Centro", "Norte"], size=N_ANULACIONES),
        }
    )

    ventas = pd.concat([df, anulaciones], ignore_index=True)
    ventas = ventas.sample(frac=1.0, random_state=semilla).reset_index(drop=True)
    ventas.insert(0, "venta_id", [f"V{i:04d}" for i in range(1, len(ventas) + 1)])
    ventas["fecha"] = pd.to_datetime(ventas["fecha"]).dt.strftime("%Y-%m-%d")

    request_id = "req-" + hashlib.sha1(f"aromaandino-{semilla}".encode()).hexdigest()[:12]
    carga = {
        "meta": {
            "endpoint": "https://pos.aromaandino.co/api/v2/ventas",
            "metodo": "GET",
            "parametros": {
                "desde": (corte - pd.Timedelta(days=dias)).strftime("%Y-%m-%d"),
                "hasta": (corte - pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                "sedes": ["Centro", "Norte"],
            },
            "request_id": request_id,
            "descargado": corte.strftime("%Y-%m-%d") + "T06:15:00-05:00",
            "registros": len(ventas),
            "pagina": 1,
            "paginas": 1,
            "nota": "Incluye anulaciones y reversas del POS (cantidad <= 0).",
        },
        "data": ventas.to_dict(orient="records"),
    }
    destinos["ventas"].write_text(json.dumps(carga, ensure_ascii=False, indent=2), encoding="utf-8")
    return destinos
