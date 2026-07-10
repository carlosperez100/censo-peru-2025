# Censo 2025 (INEI) — Base relacional única + mapa GEMSES

Base de datos **única, relacional, ligera** que incorpora **toda** la información de los
Tabulados de Población del Censo Nacional 2025 (INEI), lista para consultar y **enlazar
con cualquier proyecto GEMSES** por unidad geográfica — más un **mapa coroplético
interactivo** del Perú con marca GEMSES.

## 🗺️ Mapa interactivo (GitHub Pages)
**→ https://carlosperez100.github.io/censo-peru-2025/**

Réplica del visor del INEI por departamento, alimentada por `censo2025.db`, con el
**Modelo GEMSES**. Indicadores seleccionables: población, densidad (hab/km²), % mujeres,
% urbana, % rural, índice de masculinidad. Página autocontenida (`index.html`, sin
dependencias externas); se regenera con `python mapa_gemses/generar_mapa.py`.

Fuente oficial: <https://censos2025.inei.gob.pe> → Cuadros estadísticos → Tabulados → Población.

## Qué se construyó

| Artefacto | Qué es |
|---|---|
| `censo2025.db` | **SQLite** (~26 MB, ~9 MB comprimido). 8 temas · 63 cuadros · **648.198 datos** |
| `raw/*.xlsx` | Los 8 libros oficiales descargados del INEI (6,9 MB) |
| `etl_censo2025.py` | ETL reproducible: Excel cruzado → formato largo → star schema + grafo |
| `DICCIONARIO.md` | Diccionario de datos (tablas, temas y todos los cuadros) |
| `consultas_ejemplo.sql` | 9 consultas de ejemplo (JOIN, jerarquía, recursivas) |
| `grafo/ubigeo.json` | Jerarquía geográfica como grafo (nodos/aristas) |
| `../../../gemses-grafos/grafos_censo2025/graphify-out/graph.json` | Grafo registrado en el grafo global GEMSES (2.106 nodos, 2.104 aristas) |

## Método (por qué así)

Los tabulados del INEI son **cuadros ya agregados** en Excel, con cabeceras combinadas
multinivel y notas al pie. El método más adecuado para "todo en una base relacional que
no pese, con JOINs, para proyectos futuros" es un **modelo dimensional (star schema)** en
**SQLite** + una **capa de grafo** para la jerarquía geográfica:

```
DIMENSIONES            HECHOS                        GRAFO
  tema (8)             dato (648.198)                 Perú
  cuadro (63)            = cuadro × fila × columna      └─ Departamento
  dim_ubigeo (2.097)              × valor                   └─ Provincia
  dim_fila (etiquetas)                                          └─ Distrito
  dim_columna (cabeceras)
```

- **Sin pérdida**: cada celda numérica de cada cuadro se guarda con su etiqueta de fila y
  su ruta de cabecera (desanidando celdas combinadas). Nada se resume ni se descarta.
- **Ligera**: al factorizar etiquetas y columnas en tablas de dimensión, 648K datos caben
  en ~26 MB (los mismos datos en formato ancho repetido pesaban 77 MB).
- **Geografía real**: `dim_ubigeo` reconstruye Perú → 26 unidades de 1.er nivel (incluye
  Callao, Lima Metropolitana y Región Lima) → 192 provincias → 1.878 distritos, con
  puntero `padre_id` (= árbol/grafo).

## Cómo consultar

```bash
sqlite3 censo2025.db < consultas_ejemplo.sql
```
```python
import sqlite3, pandas as pd
con = sqlite3.connect("censo2025.db")
pd.read_sql("SELECT ubigeo_nombre, valor FROM v_dato_geo "
            "WHERE hoja='INDDEM01' AND columna='Total' AND ubigeo_nivel='departamento' "
            "ORDER BY valor DESC", con)
```

Vistas listas: **`v_dato`** (dato + tema + cuadro + textos) y **`v_dato_geo`** (con
geografía resuelta por nombre a nivel nacional/departamento/provincia).

## Enlazar con otros proyectos — indexado por UBIGEO
Cada unidad de `dim_ubigeo` tiene su **código UBIGEO oficial del INEI** (`ubigeo_inei`, 6
dígitos DDPPDD), resuelto por emparejamiento jerárquico contra `ref/ubigeo_inei.csv`.
Cobertura **2103/2113 (99,5 %)**: 26 departamentos, 194 provincias y 1 882 distritos —
sin códigos duplicados. Los 10 pendientes son **distritos creados después del catálogo 2020**
(p. ej. Alto Trujillo); su plantilla está en `ref/ubigeo_pendientes.csv` y se completan en
`ref/ubigeo_overrides.csv`. Así cualquier sistema (SISOL, IPRESS, turismo, salud) enlaza con
el censo por `ubigeo_inei` a nivel departamento/provincia/distrito.

## Reproducir
```bash
python etl_censo2025.py                 # reconstruye censo2025.db desde raw/
python ../../../gemses-grafos/grafos_censo2025/build_grafo_censo.py   # regenera el grafo
```

## Pendientes / mejoras
1. ✅ **Código UBIGEO oficial** en `dim_ubigeo` (99,5 %); completar los 10 distritos nuevos en
   `ref/ubigeo_overrides.csv`.
2. Incorporar Tabulados de **Vivienda**, **Hogar** y **Comunidades Indígenas** (mismo método).
3. Drill-down del mapa a provincia/distrito usando `ubigeo_inei`.
4. Vistas curadas por dimensión (sexo/edad/área) para los cuadros demográficos clave.
