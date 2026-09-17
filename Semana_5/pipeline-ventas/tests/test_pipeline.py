"""Pruebas automatizadas del pipeline.

Cubren las propiedades que el proyecto promete:

* el KPI y el número de filas de la capa curated son los esperados;
* dos ejecuciones consecutivas producen el mismo hash (determinismo);
* la carga es idempotente (re-ejecutar no duplica registros);
* la cuarentena aísla exactamente los registros defectuosos;
* las reglas con acción DETENER (esquema, unicidad) detienen el proceso;
* la regla de rangos envía a cuarentena una llave foránea inexistente;
* la regla de frescura registra la advertencia sin detener la ejecución.

Ejecución: ``pytest`` desde la raíz del repositorio.
"""

from __future__ import annotations

import sqlite3

import pandas as pd
import pytest

from src.config import leer_config, ruta
from src.extract import extract
from src.load import load
from src.pipeline import run_pipeline
from src.transform import transform
from src.validate import ErrorDeValidacion, validate


@pytest.fixture(scope="session")
def cfg():
    """Configuración real del proyecto."""
    return leer_config()


@pytest.fixture(scope="session")
def resumen(cfg):
    """Una ejecución completa del pipeline, compartida por las pruebas."""
    return run_pipeline(cfg)


@pytest.fixture()
def enriq(cfg):
    """La tabla integrada, reconstruida desde la capa raw."""
    return transform(extract(cfg), cfg)


def test_kpi_y_filas_esperados(resumen):
    """La capa curated tiene 412 filas y un ingreso total de $606.000."""
    assert resumen["filas"] == 412
    assert resumen["ingreso_total"] == 606_000


def test_determinismo_dos_ejecuciones(cfg, resumen):
    """Dos ejecuciones consecutivas producen exactamente el mismo hash."""
    assert run_pipeline(cfg)["hash"] == resumen["hash"]


def test_carga_idempotente(cfg, enriq, resumen):
    """Re-ejecutar la carga no duplica registros en SQLite."""
    valido, _ = validate(enriq, cfg)
    load(valido, cfg)
    load(valido, cfg)  # segunda carga sobre la misma tabla
    with sqlite3.connect(ruta(cfg, "db")) as con:
        n = con.execute("SELECT COUNT(*) FROM ventas").fetchone()[0]
    assert n == resumen["filas"]


def test_cuarentena_aisla_defectos(cfg, resumen):
    """Los 14 registros con cantidad <= 0 quedan aislados por la regla de rangos."""
    q = pd.read_csv(ruta(cfg, "quarantine") / "ventas_rechazadas.csv")
    assert resumen["cuarentena"] == 14
    assert len(q) == 14
    assert (q["regla"] == "rangos").all()
    assert (q["cantidad"] <= 0).all()


def test_esquema_detiene(cfg, enriq):
    """Eliminar una columna esperada detiene el pipeline (acción DETENER)."""
    with pytest.raises(ErrorDeValidacion, match="Esquema"):
        validate(enriq.drop(columns=["ingreso"]), cfg)


def test_unicidad_detiene(cfg, enriq):
    """Un venta_id duplicado detiene el pipeline (acción DETENER)."""
    duplicado = pd.concat([enriq, enriq.head(3)], ignore_index=True)
    with pytest.raises(ErrorDeValidacion, match="Unicidad"):
        validate(duplicado, cfg)


def test_fk_inexistente_va_a_cuarentena(cfg, enriq):
    """Un cliente_id fuera de stg_clientes se aísla por la regla de rangos."""
    alterado = enriq.copy()
    fila_valida = alterado.index[alterado["cantidad"] > 0][0]
    alterado.loc[fila_valida, "cliente_id"] = "C999"
    valido, reporte = validate(alterado, cfg)
    assert reporte["reglas"]["rangos"]["filas"] == 15  # 14 de rango + 1 de FK
    assert "C999" not in set(valido["cliente_id"])


def test_frescura_advierte_sin_detener(cfg, enriq):
    """Datos por fuera del umbral de frescura generan advertencia, no error."""
    viejo = enriq.copy()
    viejo["fecha"] = viejo["fecha"] - pd.Timedelta(days=10)
    _, reporte = validate(viejo, cfg)
    assert any("Frescura" in a for a in reporte["advertencias"])
