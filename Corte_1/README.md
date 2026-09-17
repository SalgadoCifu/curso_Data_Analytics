# Data Analytics — Repositorio de Prácticas

Repositorio dedicado a la consolidación de talleres, laboratorios y proyectos de la asignatura **Data Analytics**. El contenido abarca desde los fundamentos de programación en Python hasta la manipulación de datos tabulares, cálculo de KPIs, visualización descriptiva, análisis de riesgo aplicado y pipelines de datos reproducibles (ETL).

---

## Objetivo

Desarrollar habilidades técnico-analíticas mediante la resolución de problemas aplicados, utilizando **Python** y sus librerías especializadas para la limpieza, transformación, análisis exploratorio de datos, construcción de pipelines y comunicación de métricas de negocio.

---

## Tecnologías Utilizadas

* **Lenguaje:** Python
* **Librerías:** Pandas, NumPy, Matplotlib, Seaborn, SQLite, PyYAML, pytest
* **Entornos:** Jupyter Notebook / Google Colab
* **Formatos de datos:** CSV, JSON, HTML, Parquet, SQLite

---

## Contenido por Semana

### Semana 1: Fundamentos de Python
* Configuración del entorno en Google Colab y Jupyter.
* Sintaxis básica, tipos de datos y estructuras de control.
* Lógica inicial para el procesamiento de información.

### Semana 2: Manipulación de Datos y Métricas (Restaurant Analytics)
* Análisis tabular de datos con la librería Pandas.
* Consolidación de múltiples fuentes (productos, clientes, ventas de dos semanas).
* Agregaciones, filtrados y agrupaciones (`groupby`).
* Cálculo de indicadores de ingresos, frecuencia de compra y recurrencia de clientes.
* Visualización de resultados con Matplotlib e informe ejecutivo de una página.

### Semana 4: Risk Management & OSH Analytics
* Laboratorio aplicado sobre gestión de riesgo y seguridad y salud en el trabajo (OSH).
* Consolidación de datos de trabajadores, empresas y accidentes mediante *joins* múltiples.
* Construcción de variables de riesgo y análisis de patrones de accidentalidad laboral.
* Visualización con Matplotlib y Seaborn, e informe de hallazgos.

### Semana 5: Integración de Datos y Pipeline ETL (pipeline-ventas)
* Fundamentos de integración de datos y ETL en la era del Big Data.
* Caso aplicado: pipeline analítico reproducible para un punto de venta piloto (Aroma Andino S.A.S.), que resuelve un problema real de cargas no idempotentes.
* Arquitectura por capas: `raw` → `staging` → `curated`, con cuarentena de datos rechazados.
* Extracción desde múltiples formatos de origen (API/JSON, HTML, CSV).
* Validación con reglas declaradas, carga idempotente con verificación por hash, diccionario de datos y documento de linaje.
* Suite de pruebas automatizadas con `pytest`.

---

## Estructura del Repositorio

```text
.
├── semana_1/     # Material y taller introductorio
├── semana_2/     # Laboratorio práctico de análisis con Pandas
├── semana_4/     # Laboratorio de análisis de riesgo laboral (OSH)
└── Semana_5/     # Pipeline ETL reproducible y caso de integración de datos
```
