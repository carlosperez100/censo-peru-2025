-- ============================================================================
--  CONSULTAS DE EJEMPLO  -  censo2025.db  (Censo 2025 INEI, Tabulados Poblacion)
--  Uso:  sqlite3 censo2025.db < consultas_ejemplo.sql
--  o en Python:  import sqlite3; con=sqlite3.connect('censo2025.db')
-- ============================================================================

-- 1) Poblacion total del Peru (control: 32,706,028)
SELECT valor FROM v_dato
WHERE hoja='INDDEM01' AND etiqueta_fila='PERÚ' AND columna='Total';

-- 2) Poblacion por departamento (nivel primer orden), ordenada
SELECT ubigeo_nombre AS departamento, valor AS poblacion
FROM v_dato_geo
WHERE hoja='INDDEM01' AND columna='Total' AND ubigeo_nivel='departamento'
ORDER BY poblacion DESC;

-- 3) Que cuadros hay sobre un tema (p.ej. seguro de salud)
SELECT cod_tema, hoja, titulo FROM cuadro
WHERE titulo LIKE '%seguro%' OR titulo LIKE '%salud%';

-- 4) Buscar cualquier indicador por texto libre (columna o fila)
SELECT tema, hoja, etiqueta_fila, columna, valor
FROM v_dato
WHERE columna LIKE '%alfabet%'
LIMIT 20;

-- 5) Jerarquia geografica: provincias de un departamento
SELECT nombre AS provincia FROM dim_ubigeo
WHERE padre_id=(SELECT ubigeo_id FROM dim_ubigeo WHERE nombre_norm='amazonas')
ORDER BY nombre;

-- 6) Distritos de una provincia (ruta descendente en el grafo)
SELECT d.nombre AS distrito
FROM dim_ubigeo d
JOIN dim_ubigeo p ON p.ubigeo_id=d.padre_id
WHERE p.nombre_norm='chachapoyas' AND d.nivel='distrito'
ORDER BY d.nombre;

-- 7) Recorrido ascendente (a que dep/prov pertenece un distrito)
WITH RECURSIVE sube(id,nombre,nivel,padre) AS (
  SELECT ubigeo_id,nombre,nivel,padre_id FROM dim_ubigeo WHERE nombre_norm='barranca' AND nivel='provincia'
  UNION ALL
  SELECT u.ubigeo_id,u.nombre,u.nivel,u.padre_id
  FROM dim_ubigeo u JOIN sube s ON u.ubigeo_id=s.padre
)
SELECT nivel, nombre FROM sube;

-- 8) Todo lo que el censo dice de un lugar (JOIN por nombre a todos los cuadros)
SELECT tema, hoja, columna, valor
FROM v_dato
WHERE etiqueta_norm='arequipa'
LIMIT 30;

-- 9) Catalogo: cuantos datos aporta cada tema
SELECT t.nombre AS tema, COUNT(*) AS datos
FROM dato d JOIN cuadro c ON c.cuadro_id=d.cuadro_id JOIN tema t ON t.cod_tema=c.cod_tema
GROUP BY t.nombre ORDER BY datos DESC;
