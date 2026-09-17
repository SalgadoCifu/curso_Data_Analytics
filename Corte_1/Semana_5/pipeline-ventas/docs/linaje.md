# Linaje de datos · columna → transformación → fuente

Cada columna de la capa curated se rastrea hasta el archivo crudo que la
originó. Cualquier cifra de un informe construido sobre `curated/ventas`
puede seguirse por esta tabla hasta su fuente. Herramientas como dbt
automatizan este registro a escala; la idea es exactamente la misma.

| Columna curated | Transformación | Nodo staging | Fuente raw |
|---|---|---|---|
| `venta_id` | tiquete del POS; tipado a texto, verificación de unicidad | `stg_ventas` | `ventas_api.json` (POS) |
| `fecha` | conversión a `datetime`, verificación de ventana | `stg_ventas` | `ventas_api.json` (POS) |
| `cliente_id` | normalización; verificado como FK contra clientes | `stg_ventas` ⋈ `stg_clientes` | `ventas_api.json` (POS) · `clientes.html` (CRM) |
| `producto_id` | normalización; join con el catálogo | `stg_ventas` ⋈ `stg_productos` | `ventas_api.json` (POS) · `productos.csv` (ERP) |
| `producto` | tomado del catálogo por `producto_id` | `stg_productos` | `productos.csv` (ERP) |
| `categoria` | tomada del catálogo por `producto_id` | `stg_productos` | `productos.csv` (ERP) |
| `sede` | normalización de texto | `stg_ventas` | `ventas_api.json` (POS) |
| `cantidad` | tipado a entero; regla `cantidad > 0` | `stg_ventas` | `ventas_api.json` (POS) |
| `precio_unitario` | tipado a entero; join con el catálogo | `stg_productos` | `productos.csv` (ERP) |
| `costo_unitario` | tipado a entero; join con el catálogo | `stg_productos` | `productos.csv` (ERP) |
| `ingreso` | **derivada**: `cantidad × precio_unitario` | integración (`ventas_enriq`) | `ventas_api.json` (POS) · `productos.csv` (ERP) |
| `margen` | **derivada**: `ingreso − cantidad × costo_unitario` | integración (`ventas_enriq`) | `ventas_api.json` (POS) · `productos.csv` (ERP) |

## Ramas del flujo

- **Rama de rechazo**: las filas que incumplen las reglas de contenido se
  aíslan en `data/quarantine/ventas_rechazadas.csv`, con la columna
  `regla` que indica cuál las rechazó. Se conservan y se reportan; no se
  eliminan en silencio.
- **Artefactos automáticos**: `docs/data_dictionary.md` se regenera desde
  la capa curated en cada ejecución del pipeline.
