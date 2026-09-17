# pipeline-ventas · Aroma Andino S.A.S.

Pipeline analítico del **punto de venta piloto** de Aroma Andino S.A.S.
(operador de cafeterías corporativas; barras **Centro** y **Norte**).
Repositorio de referencia del área de Analítica de Datos: toda cifra
reportada sobre el punto piloto debe poder reproducirse desde aquí con un
solo comando.

## 1 · La discrepancia que motiva el pipeline

Un análisis ad hoc del área calculaba el ingreso del período con un notebook
sin estructura. Se ejecutó dos veces, sin cambiar una línea, y el indicador
reportado cambió:

| | filas | ingreso total |
|---|---:|---:|
| 1.ª ejecución | 412 | $ 606.000 |
| 2.ª ejecución | 824 | $ 1.212.000 |

La causa raíz fue una carga no idempotente (`if_exists="append"`). La
discrepancia se reproduce en
[`discrepancia/notebook_discrepancia.ipynb`](discrepancia/notebook_discrepancia.ipynb),
que es el **punto de partida del caso**: funciona sobre una copia recién
descargada (su primera celda garantiza el snapshot de fuentes) y no requiere
haber ejecutado el pipeline antes. Este repositorio implementa el proceso que
previene la recurrencia: con el pipeline, ambas ejecuciones producen 412
filas, $ 606.000 y el **mismo hash**.

## 2 · Fuentes de datos

| Fuente | Sistema origen | Archivo en `data/raw` |
|---|---|---|
| Movimientos de venta | API del POS (`GET /api/v2/ventas`) | `ventas_api.json` |
| Clientes del programa Aroma+ | Exporte del portal CRM | `clientes.html` |
| Catálogo de productos | Exporte del ERP | `productos.csv` |

El extracto del POS incluye las **anulaciones y reversas** del período
(movimientos con `cantidad ≤ 0`), que el pipeline aísla en cuarentena en
lugar de descartarlas en silencio.

## 3 · Estructura del repositorio

```
pipeline-ventas/
├─ config.yaml               parámetros, no secretos (rutas, semilla, corte, umbrales)
├─ requirements.txt          entorno declarado con versiones fijadas
├─ README.md                 este archivo: el orden exacto de los comandos
├─ data/
│   ├─ raw/                  datos crudos, inmutables (fuentes tal como llegaron)
│   ├─ staging/              tipado y limpio (Parquet)           [generada]
│   ├─ curated/              publicable: Parquet, CSV y SQLite   [generada]
│   └─ quarantine/           filas rechazadas, contadas y con su regla [generada]
├─ src/
│   ├─ config.py             raíz del proyecto y lectura de config.yaml
│   ├─ respaldo_fuentes.py   snapshot determinista de las fuentes del período
│   ├─ extract.py            raw → DataFrames fieles a la fuente
│   ├─ transform.py          staging tipado + integración (ingreso, margen)
│   ├─ validate.py           cinco reglas con acción declarada + cuarentena
│   ├─ load.py               carga idempotente + hash de verificación
│   ├─ dictionary.py         diccionario de datos generado desde el dataset
│   └─ pipeline.py           orquestación: extract → transform → validate → load
├─ tests/
│   └─ test_pipeline.py      8 pruebas automatizadas (pytest)
├─ docs/
│   ├─ data_dictionary.md    diccionario de datos                 [generado]
│   └─ linaje.md             linaje columna → transformación → fuente
└─ discrepancia/
    └─ notebook_discrepancia.ipynb   punto de partida: la discrepancia (ejecutado)
```

Cada capa de datos es una promesa: **raw** garantiza fidelidad a la fuente,
**staging** garantiza tipos correctos y **curated** garantiza datos listos
para el análisis, sin verificación adicional.

## 4 · Requisitos e instalación

Python ≥ 3.10. Desde la raíz del repositorio:

```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Para VS Code, el repositorio incluye `.vscode/settings.json`, que hace que
los notebooks ejecuten desde la raíz del proyecto y habilita el panel de
pruebas (pytest). En cualquier caso, la primera celda del notebook ubica la
raíz por sí sola.

## 5 · Ejecución

Un solo comando reproduce todo:

```bash
python -m src.pipeline
```

Salida esperada (verificada):

```
── Resumen de la ejecución ─────────────────────────────
  filas en curated : 412
  ingreso total    : $ 606.000
  margen total     : $ 362.200
  en cuarentena    : 14 filas (data/quarantine)
  hash SHA-256     : 4b05c302ca7f064f14126d5f966b764c961fe93f136f52929b78d2ecb548698a
  Verificación: ejecutar de nuevo y comparar el hash.
```

La capa raw es inmutable: el pipeline solo la escribe si no existe. En
entornos sin acceso a la red corporativa (sandbox, CI, revisión externa),
`src/respaldo_fuentes.py` reconstruye el snapshot del período; su
regeneración es una operación explícita:

```bash
python -m src.pipeline --regenerar-fuentes
```

## 6 · Verificación de reproducibilidad

El criterio de verificación es un **hash**: una "huella digital" de 64
caracteres que resume el contenido de la tabla final. Si el contenido cambia
en un solo dato, la huella cambia por completo; si el contenido es idéntico,
la huella es idéntica. Así, en lugar de comparar 412 filas a ojo, se comparan
dos huellas.

Antes de calcularla, la tabla se lleva siempre a una misma forma estándar
(filas ordenadas por `venta_id`, columnas en orden fijo, fechas en formato
ISO), para que la huella dependa solo del contenido de los datos y no de cómo
estén escritos. Ese cálculo vive en la función `hash_canonico` del archivo
`src/load.py`.

La prueba práctica: dos ejecuciones consecutivas deben imprimir la misma
huella.

```bash
python -m src.pipeline | grep hash
python -m src.pipeline | grep hash    # mismo hash → mismo análisis
```

Las tres fuentes de irreproducibilidad están controladas por diseño: las
**rutas** son relativas a la raíz declarada en `src/config.py`; el **azar**
está gobernado por la semilla de `config.yaml`; el **tiempo** es un parámetro
(`fecha_corte`), no el reloj de la máquina.

## 7 · Validaciones y acciones

Cinco reglas corren en cada ejecución dentro de `validate()`; cada una declara
su umbral y su acción — nada queda a criterio del momento:

| Regla | Qué verifica | Acción si falla |
|---|---|---|
| `esquema` | Columnas esperadas con el tipo correcto | **DETENER** |
| `unicidad` | `venta_id` (tiquete del POS) sin duplicados | **DETENER** |
| `no_nulos` | Campos críticos completos (umbral 0 %) | **CUARENTENA** |
| `rangos` | `cantidad > 0` · fecha en ventana · FK de cliente | **CUARENTENA** |
| `frescura` | máx(fecha) a ≤ 7 días del corte | **ADVERTIR** |

En el período analizado, las 14 anulaciones y reversas del POS
(`cantidad ≤ 0`) quedan aisladas en `data/quarantine/ventas_rechazadas.csv`,
con la columna `regla` que indica cuál las rechazó. Se conservan y se
reportan como limitación declarada; no se eliminan en silencio.

## 8 · Documentación generada

- [`docs/data_dictionary.md`](docs/data_dictionary.md) se **regenera en cada
  ejecución** desde la capa curated: tipo, % de nulos y cardinalidad se
  derivan del dato; el único campo manual son las descripciones en
  `src/dictionary.py`. Una columna nueva aparece automáticamente como
  `PENDIENTE`, señalando documentación faltante.
- [`docs/linaje.md`](docs/linaje.md) declara el linaje de cada columna:
  columna → transformación → fuente (POS, CRM, ERP).

## 9 · Pruebas automatizadas

```bash
pytest
```

Ocho pruebas cubren las propiedades prometidas: KPI y filas esperados,
determinismo entre ejecuciones (mismo hash), idempotencia de la carga,
aislamiento correcto de la cuarentena, detención por esquema inválido,
detención por unicidad violada, cuarentena de llaves foráneas inexistentes y
advertencia de frescura sin detención. Resultado verificado: `8 passed`.

## 10 · Decisiones y limitaciones

- **Snapshot de fuentes.** `src/respaldo_fuentes.py` reconstruye de forma
  determinista el extracto del período para entornos sin red corporativa. En
  producción, `extract` consume la API del POS y el portal CRM; el resto del
  pipeline no cambia.
- **Anulaciones y reversas.** Son movimientos legítimos del POS; el pipeline
  no los borra: los aísla, los cuenta y los reporta. Su tratamiento contable
  queda fuera del alcance de la capa curated de ventas efectivas.
- **Cuarentena por regla única.** Cada fila rechazada se atribuye a la primera
  regla que incumple (prioridad: `no_nulos` → `rangos`).
- **Sin credenciales versionadas.** El snapshot no requiere autenticación. La
  conexión productiva usa un `.env` (nunca versionado) con su
  `.env.example` correspondiente.

## 11 · Glosario rápido

| Término | En pocas palabras |
|---|---|
| **Pipeline** | Cadena de pasos que convierte fuentes crudas en datos listos, siempre en el mismo orden. |
| **Idempotente** | Ejecutarlo N veces deja todo igual que ejecutarlo una vez (por eso `replace` y no `append`). |
| **Determinista** | Mismas entradas y parámetros → siempre el mismo resultado. |
| **Semilla (seed)** | Número fijo que hace repetible cualquier operación con azar. |
| **Capa raw / staging / curated** | Fuentes tal como llegaron / tipadas y limpias / listas para analizar. |
| **Cuarentena** | Bandeja de revisión: las filas que incumplen una regla se apartan, se cuentan y se reportan; no se borran. |
| **FK (llave foránea)** | El cliente de cada venta debe existir en la tabla de clientes. |
| **Hash** | Huella digital del contenido de la tabla final; misma huella = mismos datos. |
| **Linaje** | Registro de dónde viene cada columna: fuente → transformación → curated. |
| **Snapshot de fuentes** | Copia fija del extracto del período, para trabajar sin acceso a la red corporativa. |

## 12 · Regla general

Todo paso del proceso queda registrado en código o en configuración; de lo
contrario no es reproducible ni auditable. Los cinco antipatrones que anulan
esta base — sobrescribir la capa raw, limpieza manual, rutas absolutas,
`except: pass` y documentación tardía — están excluidos por construcción.
