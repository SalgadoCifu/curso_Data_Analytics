# Diccionario de datos · capa curated

Archivo **generado por el pipeline** en cada ejecución (`python -m src.pipeline`). No se edita a mano: la única fuente manual son las descripciones en `src/dictionary.py`.

| columna | tipo | nulos % | únicos | descripción |
|---|---|---:|---:|---|
| `venta_id` | `string` | 0.0 | 412 | Número de tiquete del POS; identificador único (llave primaria). |
| `producto_id` | `string` | 0.0 | 9 | Código del producto; verificado contra el catálogo. |
| `cantidad` | `int64` | 0.0 | 2 | Unidades vendidas; siempre mayor que cero tras la validación. |
| `fecha` | `datetime64[ns]` | 0.0 | 30 | Fecha de la venta, dentro de la ventana de análisis. |
| `cliente_id` | `string` | 0.0 | 60 | Cliente del programa Aroma+; verificado contra stg_clientes (FK). |
| `sede` | `string` | 0.0 | 2 | Barra del punto piloto donde se registró la venta (Centro o Norte). |
| `producto` | `string` | 0.0 | 9 | Nombre comercial del producto (del catálogo). |
| `categoria` | `string` | 0.0 | 3 | Categoría del producto (del catálogo). |
| `precio_unitario` | `int64` | 0.0 | 5 | Precio de venta por unidad, en COP (del catálogo). |
| `costo_unitario` | `int64` | 0.0 | 9 | Costo por unidad, en COP (del catálogo). |
| `ingreso` | `int64` | 0.0 | 7 | Variable derivada: cantidad × precio_unitario. |
| `margen` | `int64` | 0.0 | 15 | Variable derivada: ingreso − cantidad × costo_unitario. |
