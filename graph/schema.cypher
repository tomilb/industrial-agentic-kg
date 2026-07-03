// Constraints e índices del grafo de planta (ver ARCHITECTURE.md).
// Todas las sentencias usan IF NOT EXISTS: ejecutar este fichero varias
// veces no falla ni duplica nada.

CREATE CONSTRAINT linea_id_unique IF NOT EXISTS
FOR (l:Linea) REQUIRE l.id IS UNIQUE;

CREATE CONSTRAINT estacion_id_unique IF NOT EXISTS
FOR (e:Estacion) REQUIRE e.id IS UNIQUE;

CREATE CONSTRAINT maquina_id_unique IF NOT EXISTS
FOR (m:Maquina) REQUIRE m.id IS UNIQUE;

CREATE CONSTRAINT maquina_candidata_id_unique IF NOT EXISTS
FOR (c:MaquinaCandidata) REQUIRE c.id IS UNIQUE;

// RegistroProduccion no tiene id propio (ver ARCHITECTURE.md): su clave
// natural es (Maquina)-[:REGISTRA]->(fecha), que load_data.py resuelve
// con MERGE sobre el patrón completo. Este índice solo acelera las
// consultas por rango de fechas (p.ej. detectar_cuello_botella).
CREATE INDEX registro_produccion_fecha_idx IF NOT EXISTS
FOR (r:RegistroProduccion) ON (r.fecha);
