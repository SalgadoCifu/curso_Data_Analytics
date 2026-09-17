"""Orquestación del pipeline: un solo comando reproduce todo.

Uso::

    python -m src.pipeline                      # ejecución normal
    python -m src.pipeline --regenerar-fuentes  # regenera la capa raw

La secuencia de ejecución está definida aquí — no depende del orden manual
de celdas ni de conocimiento implícito::

    extract → transform → validate → load → diccionario

``validate`` precede a ``load`` por diseño: los datos inválidos se
detectan antes de la carga, no después. El resumen final imprime el hash
de la capa curated; dos ejecuciones consecutivas deben producir el mismo
valor (criterio de reproducibilidad).
"""

from __future__ import annotations

import argparse
import sys
from typing import Any

from .config import leer_config
from .dictionary import escribir_diccionario
from .extract import extract
from .respaldo_fuentes import generar_fuentes
from .load import load
from .transform import transform
from .validate import ErrorDeValidacion, validate


def run_pipeline(cfg: dict[str, Any]) -> dict[str, Any]:
    """Ejecuta el pipeline de extremo a extremo y devuelve el resumen.

    Args:
        cfg: Configuración cargada desde ``config.yaml``.

    Returns:
        Resumen de la ejecución (filas, KPI, hash, cuarentena y
        advertencias).

    Raises:
        ErrorDeValidacion: si una regla con acción DETENER falla; en ese
            caso ningún dato llega a la capa curated.
    """
    generar_fuentes(cfg)                    # snapshot: solo escribe si raw no existe
    crudo = extract(cfg)                    # raw → DataFrames fieles a la fuente
    enriq = transform(crudo, cfg)           # staging tipado + integración
    valido, reporte = validate(enriq, cfg)  # detiene aquí si algo falla
    resumen = load(valido, cfg)             # ningún dato inválido llega a curated
    resumen["diccionario"] = escribir_diccionario(valido, cfg)
    resumen["cuarentena"] = reporte["filas_cuarentena"]
    resumen["advertencias"] = reporte["advertencias"]
    return resumen


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de línea de comandos."""
    parser = argparse.ArgumentParser(description="Pipeline reproducible del caso de ventas.")
    parser.add_argument(
        "--regenerar-fuentes",
        action="store_true",
        help="Reescribe el snapshot de fuentes (operación explícita; raw es inmutable).",
    )
    args = parser.parse_args(argv)

    cfg = leer_config()
    if args.regenerar_fuentes:
        generar_fuentes(cfg, forzar=True)

    try:
        r = run_pipeline(cfg)
    except ErrorDeValidacion as exc:
        print(f"[DETENIDO] {exc}", file=sys.stderr)
        return 1

    print("── Resumen de la ejecución ─────────────────────────────")
    print(f"  filas en curated : {r['filas']}")
    print(f"  ingreso total    : $ {r['ingreso_total']:,}".replace(",", "."))
    print(f"  margen total     : $ {r['margen_total']:,}".replace(",", "."))
    print(f"  en cuarentena    : {r['cuarentena']} filas (data/quarantine)")
    for adv in r["advertencias"]:
        print(f"  [ADVERTENCIA] {adv}")
    print(f"  hash SHA-256     : {r['hash']}")
    print("  Verificación: ejecutar de nuevo y comparar el hash.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
