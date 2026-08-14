# Restaurant Analytics – Business Data Analytics Applied Lab

Este repositorio contiene el desarrollo del laboratorio aplicado de la asignatura Data Analytics (Código: 43390860), correspondiente a la semana 2 del curso. El objetivo es consolidar datos de una cadena de restaurantes, construir indicadores comerciales y generar recomendaciones estratégicas a partir de un análisis reproducible.

## Objetivo del proyecto
Consolidar cuatro fuentes de datos independientes (productos, clientes y ventas de dos semanas), validar las relaciones entre tablas, calcular indicadores clave de ingresos, frecuencia de compra y recurrencia de clientes, y presentar los hallazgos en un informe ejecutivo de una página.

El análisis se limita a ingresos, frecuencia y recurrencia; no se incluyen costos, cantidades, descuentos ni se calcula rentabilidad, utilidad o margen.

## Estructura del repositorio

lab-restaurant/
│
├── data/
│   ├── Restaurant-Foods.csv
│   ├── Restaurant-Customers.csv
│   ├── Restaurant-Week1-Sales.csv
│   └── Restaurant-Week2-Sales.csv
│
├── lab_Sem2_DA_20261.ipynb      # Notebook principal con el análisis
├── Informe Semana 2.pdf         # Informe ejecutivo de una página
└── README.md                    # Este archivo


## Datos utilizados
Los archivos CSV contienen:
- Restaurant-Foods.csv: Catálogo de productos con Food ID, Food Item y Price.
- Restaurant-Customers.csv: Información de clientes (ID, First Name, Last Name, Gender, Company, Occupation).
- Restaurant-Week1-Sales.csv y Restaurant-Week2-Sales.csv: Registros de ventas con Customer ID y Food ID (cada fila representa una transacción).

Nota: Los nombres de clientes no se exponen en el informe ni en las visualizaciones por privacidad.

## Requisitos e instalación
Este proyecto se ejecuta en Python 3 con las siguientes librerías:
- pandas
- sqlite3 (incluida en la biblioteca estándar)
- matplotlib

Instala las dependencias con:
pip install pandas matplotlib

Si trabajas en Google Colab, las librerías ya están preinstaladas. Para montar Google Drive, se incluye una celda opcional en el notebook.

## Instrucciones de ejecución
1. Clona este repositorio o descarga los archivos.
2. Coloca los archivos CSV en la carpeta data/.
3. Abre el notebook lab_Sem2_DA_20261.ipynb en Jupyter Notebook, JupyterLab o Google Colab.
4. Ejecuta todas las celdas en orden ascendente.
5. Si usas Colab, descomenta y ejecuta la celda de montaje de Drive para acceder a los archivos.

El notebook está diseñado para ejecutarse de forma secuencial sin modificaciones manuales, garantizando la reproducibilidad.

## Principales hallazgos

### Desempeño del menú
- El producto más vendido fue Drink (59 transacciones), pero el de mayores ingresos fue Steak ($1,249.50).
- Esto evidencia que frecuencia de compra e ingresos no son equivalentes: los artículos de alto valor pueden no ser los más pedidos, pero aportan más a la facturación.

### Comparación semanal
- Semana 1: 250 ventas, $1,962.68 de ingresos, promedio $7.85 por transacción.
- Semana 2: 250 ventas, $1,923.88 de ingresos, promedio $7.70 por transacción.
- El número de ventas se mantuvo, pero el ingreso promedio disminuyó ligeramente, reflejando un cambio en la mezcla de productos.

### Recurrencia de clientes
- Clientes únicos semana 1: 221; semana 2: 224.
- Clientes recurrentes (compraron ambas semanas): 46.
- Tasa de recurrencia: 20.8%, lo que indica que la mayoría de los clientes son ocasionales.

### Perfil por ocupación
- Las ocupaciones con mayor gasto acumulado fueron Compensation Analyst, Sales Representative y Marketing Manager.
- Este patrón sugiere que el restaurante atrae a profesionales de oficinas y áreas administrativas cercanas.

### Recomendación estratégica
- Implementar menús ejecutivos que combinen productos de alta rotación (ej. Drink, Salad) con platos de alto valor (ej. Steak, Pasta) para elevar el ticket promedio.
- Desarrollar un programa de fidelización (tarjetas de puntos, descuentos corporativos) dirigido a empresas cercanas para convertir visitantes ocasionales en clientes habituales.

## Limitaciones del análisis
- Los datos no incluyen cantidades por transacción, por lo que el número de registros se usa como proxy de frecuencia de compra.
- No se dispone de costos, descuentos ni márgenes, por lo que el análisis se restringe a ingresos y recurrencia.
- La comparación entre dos semanas no permite establecer causalidad; solo se reportan asociaciones observadas.

## Informe ejecutivo
El archivo Informe Semana 2.pdf contiene el resumen ejecutivo de una página con los gráficos y recomendaciones finales, dirigido a la gerencia del restaurante.

## Integrantes del equipo
- Diana Sofia Carrero Acero
- Paula Ximena Ortiz Acevedo
- María Valentina Salgado Cifuentes
- Santiago Villamil Marroquín

## Contacto
Para cualquier duda sobre este repositorio o el análisis, puedes abrir un issue o contactar a los autores a través de la plataforma educativa.

Este proyecto fue desarrollado como parte del curso de Data Analytics – Universidad Central