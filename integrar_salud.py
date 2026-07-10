# -*- coding: utf-8 -*-
"""
Integra a censo2025.db la OFERTA DE SALUD de SUSALUD (datos.susalud.gob.pe), enlazada por UBIGEO
con la poblacion del censo:
  - RENIPRESS  -> tabla ipress (todos los establecimientos: MINSA, EsSalud, privado, SISOL/municipal, FFAA...)
  - Recursos de Salud (ConsultaA) -> tabla salud_rrhh (medicos, enfermeras, odontologos, obstetras, camas...)
  - densidad_salud -> profesionales por 10 000 habitantes por departamento y provincia
Se ejecuta despues del ETL del censo (o se invoca desde el).
"""
import pandas as pd, sqlite3, os, unicodedata

HERE = os.path.dirname(__file__)
DB   = os.path.join(HERE, "censo2025.db")
SUS  = os.path.join(HERE, "raw", "susalud")
RENIPRESS = os.path.join(SUS, "RENIPRESS.csv")
RRHH      = os.path.join(SUS, "RecursosSalud_2026.csv")

def sector(inst):
    i = str(inst).upper()
    if "ESSALUD" in i: return "EsSalud"
    if "PRIVADO" in i: return "Privado"
    if "SANIDAD" in i: return "FFAA/Policiales"
    if "MUNICIPAL" in i: return "Municipal (incl. SISOL)"
    if "INPE" in i: return "INPE"
    if "MINSA" in i or "GOBIERNO REGIONAL" in i: return "MINSA/Gob. Regional"
    return "Otro"

def main(db=DB):
    con = sqlite3.connect(db); cx = con.cursor()

    # ---- poblacion total del censo por DD (departamento) y DDPP (provincia) ----
    pop_dd, pop_ddpp = {}, {}
    for inei, nivel, nombre, val in cx.execute("""
        SELECT u.ubigeo_inei, u.nivel, u.nombre, d.valor
        FROM dato d JOIN cuadro c ON c.cuadro_id=d.cuadro_id
             JOIN dim_fila f ON f.fila_id=d.fila_id
             JOIN dim_columna k ON k.col_id=d.col_id
             JOIN dim_ubigeo u ON u.nombre_norm=REPLACE(REPLACE(f.etiqueta_norm,'provincia ',''),'distrito ','')
        WHERE c.hoja='INDDEM06' AND k.columna='Total' AND u.ubigeo_inei IS NOT NULL
          AND (u.nivel='departamento' OR u.nivel='provincia')"""):
        if nivel == "departamento":
            pop_dd[inei[:2]] = pop_dd.get(inei[:2], 0) + (val or 0)   # Lima = Metro + Region
            if nombre == "Lima Metropolitana": pop_ddpp["1501"] = val or 0
            if nombre == "Prov. Const. del Callao": pop_ddpp["0701"] = val or 0
        else:
            pop_ddpp[inei[:4]] = val or 0

    # ---- RENIPRESS -> tabla ipress ----
    ip = pd.read_csv(RENIPRESS, sep=";", dtype=str, encoding="latin-1", on_bad_lines="skip").fillna("")
    ip["SECTOR"] = ip["INSTITUCION"].map(sector)
    ip_out = ip[["COD_IPRESS","NOMBRE","INSTITUCION","SECTOR","CLASIFICACION","CATEGORIA",
                 "UBIGEO","DEPARTAMENTO","PROVINCIA","DISTRITO","NORTE","ESTE"]].copy()
    ip_out.columns = ["cod_ipress","nombre","institucion","sector","clasificacion","categoria",
                      "ubigeo","departamento","provincia","distrito","norte","este"]
    cx.execute("DROP TABLE IF EXISTS ipress")
    ip_out.to_sql("ipress", con, index=False)

    # ---- Recursos de Salud (ultimo registro por IPRESS) -> tabla salud_rrhh ----
    rh = pd.read_csv(RRHH, sep=";", dtype=str, encoding="latin-1", on_bad_lines="skip").fillna("")
    rh["ym"] = rh["ANHO"] + rh["MES"].str.zfill(2)
    rh = rh.sort_values("ym").groupby("CO_IPRESS", as_index=False).tail(1)
    NUM = {"CA_CAMAS":"camas","CA_CONSULTORIOS":"consultorios","CA_MEDICOS_TOTAL":"medicos",
           "CA_MEDICOS_SERUM":"med_serum","CA_MEDICOS_RESIDENTES":"med_resid","CA_ENFERMERAS":"enfermeras",
           "CA_ODONTOLOGOS":"odontologos","CA_OBSTETRICES":"obstetras","CA_PSICOLOGOS":"psicologos",
           "CA_NUTRICIONISTAS":"nutricionistas","CA_TECNOLOGOS_MEDICOS":"tecnologos",
           "CA_FARMACEUTICOS":"farmaceuticos","CA_AMBULANCIAS":"ambulancias"}
    for c in NUM: rh[c] = pd.to_numeric(rh[c], errors="coerce").fillna(0).astype(int)
    rh_out = rh[["CO_IPRESS","UBIGEO","SECTOR","CATEGORIA","ANHO","MES"] + list(NUM)].copy()
    rh_out.columns = ["co_ipress","ubigeo","sector","categoria","anho","mes"] + list(NUM.values())
    cx.execute("DROP TABLE IF EXISTS salud_rrhh")
    rh_out.to_sql("salud_rrhh", con, index=False)

    # ---- densidad por 10 000 hab por departamento y provincia ----
    rh_out["dd"] = rh_out["ubigeo"].str[:2]; rh_out["ddpp"] = rh_out["ubigeo"].str[:4]
    ip_out["dd"] = ip_out["ubigeo"].str[:2]; ip_out["ddpp"] = ip_out["ubigeo"].str[:4]
    prof = ["medicos","enfermeras","odontologos","obstetras","camas"]

    cx.execute("DROP TABLE IF EXISTS densidad_salud")
    cx.execute("""CREATE TABLE densidad_salud(
        nivel TEXT, ubigeo TEXT, poblacion INT, n_ipress INT,
        medicos INT, enfermeras INT, odontologos INT, obstetras INT, camas INT,
        d_medicos REAL, d_enfermeras REAL, d_odontologos REAL, d_obstetras REAL, d_camas REAL)""")

    def cargar(nivel, key_rh, key_ip, popdic):
        agg = rh_out.groupby(key_rh)[prof].sum()
        nip = ip_out.groupby(key_ip).size()
        for key, pob in popdic.items():
            if not pob: continue
            row = agg.loc[key] if key in agg.index else None
            m = int(row["medicos"]) if row is not None else 0
            e = int(row["enfermeras"]) if row is not None else 0
            o = int(row["odontologos"]) if row is not None else 0
            ob = int(row["obstetras"]) if row is not None else 0
            ca = int(row["camas"]) if row is not None else 0
            ni = int(nip.loc[key]) if key in nip.index else 0
            f = 10000.0 / pob
            cx.execute("INSERT INTO densidad_salud VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                       (nivel, key, int(pob), ni, m, e, o, ob, ca,
                        round(m*f,2), round(e*f,2), round(o*f,2), round(ob*f,2), round(ca*f,2)))
    cargar("departamento", "dd", "dd", pop_dd)
    cargar("provincia", "ddpp", "ddpp", pop_ddpp)

    # ---- vistas ----
    cx.executescript("""
    DROP VIEW IF EXISTS v_ipress_sector;
    CREATE VIEW v_ipress_sector AS
      SELECT substr(ubigeo,1,2) AS dd, sector, COUNT(*) AS n FROM ipress GROUP BY 1,2;
    """)
    con.commit()
    # resumen
    print("  IPRESS:", cx.execute("SELECT COUNT(*) FROM ipress").fetchone()[0],
          "| RRHH IPRESS:", cx.execute("SELECT COUNT(*) FROM salud_rrhh").fetchone()[0])
    nac = cx.execute("SELECT SUM(medicos),SUM(enfermeras),SUM(odontologos),SUM(obstetras),SUM(poblacion) FROM densidad_salud WHERE nivel='departamento'").fetchone()
    print(f"  Nacional: medicos {nac[0]:,} enfermeras {nac[1]:,} odont {nac[2]:,} obstetras {nac[3]:,}")
    print(f"  Densidad nacional /10k: medicos {nac[0]/nac[4]*10000:.1f} enfermeras {nac[1]/nac[4]*10000:.1f}")
    con.close()

if __name__ == "__main__":
    main()
