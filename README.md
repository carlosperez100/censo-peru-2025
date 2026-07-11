# Censo 2025 (INEI) — Base relacional única + mapa GEMSES

Base de datos **única, relacional, ligera** que incorpora **toda** la información de los
Tabulados de Población del Censo Nacional 2025 (INEI), lista para consultar y **enlazar
con cualquier proyecto GEMSES** por unidad geográfica — más un **mapa coroplético
interactivo** del Perú con marca GEMSES.

## 🗺️ Mapa interactivo (GitHub Pages)
**→ https://carlosperez100.github.io/censo-peru-2025/**

Réplica del visor del INEI, alimentada por `censo2025.db`, con el **Modelo GEMSES**:
- **Header = recuadro oficial INEI**: Población **total** (34 157 732), **censada** (32 706 028),
  **omitida** (1 451 704), **viviendas particulares** (13 762 606) y **hogares** (10 570 171).
- **Tres capas**: *Demografía* (población total/censada, % omisión, densidad, % urbana, % mujeres,
  viviendas, hogares), **Salud — afiliación a seguro** (% con seguro, **% SIS**, **% EsSalud**,
  % sin seguro, % privado) y **Oferta de salud — SUSALUD** (**médicos, enfermeras, obstetras,
  odontólogos, camas por 10 000 hab** y n.º de IPRESS).
- **Drill-down**: clic en un departamento → mapa de sus **provincias** (con zoom), tanto para
  demografía como para salud; botón «← Perú» para volver.
- **Panel «¿Dónde están los afiliados?»**: desglose SIS / EsSalud / privado / sin seguro por unidad.
- Página autocontenida (`index.html`, sin dependencias); se regenera con
  `python mapa_gemses/generar_mapa.py`. Datos de salud: cuadro **SALUD06** vía la vista `v_seguro`.

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

## 📋 Tablas de detalle (por ubigeo, descargables)
**→ https://carlosperez100.github.io/censo-peru-2025/tablas.html**
Navegador ordenable/buscable con el detalle **por departamento (25), provincia (194) y distrito (1 892)**,
un indicador por columna, y descarga en **CSV** (`tablas/departamentos.csv`, `provincias.csv`, `distritos.csv`).
Auditado: la población por distrito suma exactamente la censada nacional (32 706 028) y cada distrito suma a
su provincia. A nivel distrito hay población + oferta (IPRESS/RR.HH.); seguro, viviendas y hogares llegan
hasta provincia/departamento en el censo.

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

## Oferta de salud (SUSALUD) — base integrada
Además del censo, la base integra por **UBIGEO** los datos de [SUSALUD](http://datos.susalud.gob.pe):
- `ipress` — **26 733 establecimientos** del RENIPRESS 2026 (MINSA/Gob. Regional, EsSalud, privados,
  municipal/SISOL, FFAA/policiales, INPE), con institución, categoría, ubigeo y coordenadas.
- `salud_rrhh` — recursos por IPRESS (Consulta A): médicos, enfermeras, odontólogos, obstetras,
  camas, consultorios, ambulancias (último registro por IPRESS).
- `densidad_salud` — **profesionales por 10 000 hab** por departamento y provincia, cruzando el
  personal con la población total del censo. Nacional: **médicos 15,9 · enfermeras 15,1** por 10k.
  Se regenera con `python integrar_salud.py` (o dentro de `etl_censo2025.py`).

> Cobertura: el módulo de recursos lo reportan sobre todo IPRESS públicas; el sector privado está
> subrepresentado en RR.HH. (aunque sí en el conteo de establecimientos).

## Enlazar con otros proyectos — indexado por UBIGEO
Cada unidad de `dim_ubigeo` tiene su **código UBIGEO oficial del INEI** (`ubigeo_inei`, 6
dígitos DDPPDD), resuelto por emparejamiento jerárquico contra `ref/ubigeo_inei.csv`.
Cobertura **2103/2113 (99,5 %)**: 26 departamentos, 194 provincias y 1 882 distritos —
sin códigos duplicados. Los 10 pendientes son **distritos creados después del catálogo 2020**
(p. ej. Alto Trujillo); su plantilla está en `ref/ubigeo_pendientes.csv` y se completan en
`ref/ubigeo_overrides.csv`. Así cualquier sistema (SISOL, IPRESS, turismo, salud) enlaza con
el censo por `ubigeo_inei` a nivel departamento/provincia/distrito.

## Fuentes (con enlace)
- **INEI · Censos Nacionales 2025** — [Tabulados de Población](https://censos2025.inei.gob.pe/resultados/descarga-de-datos/cuadros-estadisticos/tabulados/tabulados-poblacion) (cuadros INDDEM01/06, SALUD06) y [Tabulados de Vivienda](https://censos2025.inei.gob.pe/resultados/descarga-de-datos/cuadros-estadisticos/tabulados/tabulados-vivienda) (VIV1).
- **SUSALUD · Datos Abiertos** — [RENIPRESS 2026](http://datos.susalud.gob.pe/dataset/registro-nacional-de-ipress-renipress) (establecimientos) y [Recursos de Salud por IPRESS 2026](http://datos.susalud.gob.pe/dataset/consulta-recursos-de-salud-por-ipress) (RR.HH.).
- **Banco Mundial / OMS** — [Médicos por 1 000 hab (SH.MED.PHYS.ZS)](https://data.worldbank.org/indicator/SH.MED.PHYS.ZS) y [Enfermeras y parteras por 1 000 hab (SH.MED.NUMW.P3)](https://data.worldbank.org/indicator/SH.MED.NUMW.P3).
- **UBIGEO oficial** — catálogo INEI/RENIEC ([jmcastagnetto/ubigeo-peru-aumentado](https://github.com/jmcastagnetto/ubigeo-peru-aumentado)). **Geometría** — [juaneladio/peru-geojson](https://github.com/juaneladio/peru-geojson).

## Reproducir
```bash
python etl_censo2025.py                 # reconstruye censo2025.db desde raw/
python ../../../gemses-grafos/grafos_censo2025/build_grafo_censo.py   # regenera el grafo
```

## Pendientes / mejoras
1. ✅ **Código UBIGEO oficial** en `dim_ubigeo` (99,7 %); completar 6 distritos nuevos en
   `ref/ubigeo_overrides.csv`.
2. ✅ **Afiliación a seguro de salud** integrada (`v_seguro`) y mapeada (SIS/EsSalud/privado/sin seguro).
3. ✅ **Drill-down** departamento→provincia en el mapa.
4. ✅ **Oferta de salud SUSALUD** integrada (IPRESS + RR.HH.) y densidad por 10 000 hab en el mapa.
5. Incorporar Tabulados de **Hogar** y **Comunidades Indígenas**, y servicios básicos de vivienda.
6. Drill-down a **distrito** (población; salud/oferta a nivel provincia).
7. Cruce oferta vs. demanda (IPRESS/RR.HH. vs. población asegurada) por ubigeo.
