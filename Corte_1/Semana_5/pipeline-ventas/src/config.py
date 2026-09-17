"""Carga de configuración y resolución de rutas.

Este módulo define la única fuente de verdad sobre dónde está la raíz del
proyecto y cómo se leen los parámetros. Todas las rutas del pipeline son
relativas a ``ROOT``; ningún otro módulo construye rutas por su cuenta.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

#: Raíz del repositorio, declarada una sola vez (dos niveles sobre este archivo).
ROOT: Path = Path(__file__).resolve().parents[1]

#: Ruta del archivo de configuración.
CONFIG_PATH: Path = ROOT / "config.yaml"


def leer_config(path: Path | str = CONFIG_PATH) -> dict[str, Any]:
    """Lee ``config.yaml`` y devuelve el diccionario de configuración.

    Args:
        path: Ruta del archivo de configuración. Por defecto, el de la raíz.

    Returns:
        Configuración completa (secciones ``proyecto``, ``rutas``,
        ``parametros`` y ``umbrales``).

    Raises:
        FileNotFoundError: si el archivo no existe. El pipeline no asume
            valores por defecto: una configuración ausente detiene el proceso.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"No existe el archivo de configuración: {path}. "
            "El pipeline no se ejecuta con parámetros implícitos."
        )
    with open(path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def ruta(cfg: dict[str, Any], clave: str) -> Path:
    """Resuelve una ruta declarada en ``config.yaml`` contra la raíz.

    Args:
        cfg: Configuración cargada con :func:`leer_config`.
        clave: Nombre de la ruta dentro de la sección ``rutas``.

    Returns:
        Ruta absoluta correspondiente.
    """
    return ROOT / cfg["rutas"][clave]
