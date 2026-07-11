# -*- coding: utf-8 -*-
"""
Genera tablas de detalle por DEPARTAMENTO, PROVINCIA y DISTRITO (un indicador por columna),
en CSV descargable + navegador HTML (ordenable/buscable). Todo desde censo2025.db, por UBIGEO.
"""
import sqlite3, pandas as pd, json, os

HERE = os.path.dirname(__file__)
DB   = os.path.join(HERE, "..", "censo2025.db")
OUT  = os.path.join(HERE, "..", "tablas")
os.makedirs(OUT, exist_ok=True)
con = sqlite3.connect(DB)

TEMPLATE = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Censo 2025 · tablas de detalle por ubigeo — GEMSES</title>
<meta name="description" content="Tablas de detalle del Censo 2025 (INEI) y oferta de salud (SUSALUD) por departamento, provincia y distrito. Descargables en CSV. Modelo GEMSES.">
<style>
:root{--navy:#0a2e5c;--blue:#124a8f;--teal:#12a5a5;--gold:#e0a80d;--ink:#0e1c30;--muted:#5b6b82;--line:#e2e8f0;--bg:#f4f7fb;--card:#fff}
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,Arial,sans-serif;color:var(--ink);background:var(--bg)}
a{color:#2b76d1;text-decoration:none}
header{background:linear-gradient(120deg,var(--navy),var(--blue) 60%,var(--teal));color:#fff;padding:18px 22px}
.brand{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{font-weight:800;letter-spacing:2px;font-size:22px;border:2px solid var(--gold);border-radius:10px;padding:4px 12px;background:rgba(255,255,255,.06)}
.logo b{color:var(--gold)}
.htxt h1{margin:0;font-size:19px}.htxt p{margin:2px 0 0;font-size:13px;opacity:.9}
.wrap{max-width:1280px;margin:16px auto;padding:0 14px}
.bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:10px}
.tab{border:1px solid var(--line);background:#fff;color:var(--blue);border-radius:999px;padding:7px 15px;font-size:13.5px;font-weight:700;cursor:pointer}
.tab.active{background:var(--navy);color:#fff;border-color:var(--navy)}
#q{flex:1;min-width:180px;padding:8px 12px;border:1px solid var(--line);border-radius:8px;font-size:14px}
.dl{background:var(--teal);color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:700;cursor:pointer}
.count{font-size:12.5px;color:var(--muted)}
.tblwrap{overflow:auto;max-height:70vh;border:1px solid var(--line);border-radius:12px;background:#fff}
table{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums}
th,td{padding:6px 9px;border-bottom:1px solid var(--line);white-space:nowrap;text-align:right}
th{position:sticky;top:0;background:var(--navy);color:#fff;cursor:pointer;text-align:right;font-weight:600;z-index:1}
th:first-child,td:first-child,th.txt,td.txt{text-align:left}
tbody tr:hover{background:#eef3fb}
td.txt{color:var(--navy);font-weight:600}
footer{max-width:1280px;margin:10px auto 30px;padding:0 14px;font-size:12px;color:var(--muted)}
.gem{color:var(--navy);font-weight:700}
</style></head><body>
<header><div class="brand">
 <div class="logo">GEM<b>SES</b></div>
 <div class="htxt"><h1>Censo 2025 · tablas de detalle por ubigeo</h1>
 <p>Departamento · Provincia · Distrito — población (INEI) y oferta de salud (SUSALUD) ·
 <a href="index.html" style="color:#fff;text-decoration:underline">← mapa</a> ·
 <a href="comparativo.html" style="color:#fff;text-decoration:underline">Perú vs el mundo</a></p></div>
</div></header>
<div class="wrap">
 <div class="bar">
  <button class="tab active" data-k="departamento">Departamentos</button>
  <button class="tab" data-k="provincia">Provincias</button>
  <button class="tab" data-k="distrito">Distritos</button>
  <input id="q" placeholder="Buscar por nombre…">
  <button class="dl" id="dl">⬇ CSV</button>
  <span class="count" id="count"></span>
 </div>
 <div class="tblwrap"><table id="t"><thead></thead><tbody></tbody></table></div>
</div>
<footer><b>Fuentes:</b>
 <a href="https://censos2025.inei.gob.pe/resultados/descarga-de-datos/cuadros-estadisticos/tabulados/tabulados-poblacion" target="_blank" rel="noopener">INEI · Censos 2025 — Población</a> (INDDEM01/06, SALUD06),
 <a href="https://censos2025.inei.gob.pe/resultados/descarga-de-datos/cuadros-estadisticos/tabulados/tabulados-vivienda" target="_blank" rel="noopener">Vivienda</a> (VIV1);
 <a href="http://datos.susalud.gob.pe/dataset/registro-nacional-de-ipress-renipress" target="_blank" rel="noopener">SUSALUD · RENIPRESS 2026</a> y
 <a href="http://datos.susalud.gob.pe/dataset/consulta-recursos-de-salud-por-ipress" target="_blank" rel="noopener">Recursos de Salud por IPRESS 2026</a>.
 A nivel <b>distrito</b> solo hay población y oferta (seguro, viviendas y hogares llegan hasta provincia/departamento en el censo).
 Densidades por 10 000 hab. <b>Ojo:</b> a nivel distrito, «Méd./10k» refleja el <i>lugar de trabajo</i> (un distrito-polo como
 Miraflores concentra IPRESS que atienden a toda la ciudad), no la dotación por residente. CSV descargables:
 <a href="tablas/departamentos.csv">departamentos</a> ·
 <a href="tablas/provincias.csv">provincias</a> · <a href="tablas/distritos.csv">distritos</a>.
 <span class="gem">Modelo GEMSES</span> · Carlos Pérez Pérez.</footer>
<script>
const DATA=__DATA__; let lvl="departamento", sortC=1, sortD=1, filtered=[];
const files={departamento:"tablas/departamentos.csv",provincia:"tablas/provincias.csv",distrito:"tablas/distritos.csv"};
const fmt=v=>v==null?"":(typeof v==="number"?(Number.isInteger(v)?v.toLocaleString("es-PE"):v.toLocaleString("es-PE",{minimumFractionDigits:1,maximumFractionDigits:1})):v);
function render(){
 const D=DATA[lvl], qv=document.getElementById("q").value.trim().toLowerCase();
 const txtCols=D.cols.map((c,i)=>["ubigeo","departamento","provincia","distrito"].includes(c)?i:-1).filter(i=>i>=0);
 filtered=D.rows.filter(r=>!qv||txtCols.some(i=>String(r[i]??"").toLowerCase().includes(qv)));
 filtered.sort((a,b)=>{let x=a[sortC],y=b[sortC];if(x==null)return 1;if(y==null)return -1;
   if(typeof x==="number"&&typeof y==="number")return (x-y)*sortD;return String(x).localeCompare(String(y))*sortD;});
 document.querySelector("#t thead").innerHTML="<tr>"+D.lbl.map((l,i)=>{
   const tx=txtCols.includes(i)?"txt":"";const ar=i===sortC?(sortD>0?" ▲":" ▼"):"";
   return `<th class="${tx}" data-i="${i}">${l}${ar}</th>`;}).join("")+"</tr>";
 document.querySelector("#t tbody").innerHTML=filtered.map(r=>"<tr>"+r.map((v,i)=>
   `<td class="${txtCols.includes(i)?"txt":""}">${fmt(v)}</td>`).join("")+"</tr>").join("");
 document.getElementById("count").textContent=filtered.length+" filas";
 document.querySelectorAll("#t th").forEach(th=>th.addEventListener("click",()=>{
   const i=+th.dataset.i; sortD=(i===sortC)?-sortD:(["ubigeo","departamento","provincia","distrito"].includes(DATA[lvl].cols[i])?1:-1); sortC=i; render();}));
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));b.classList.add("active");
 lvl=b.dataset.k; sortC=1; sortD=1; render();}));
document.getElementById("q").addEventListener("input",render);
document.getElementById("dl").addEventListener("click",()=>{window.location=files[lvl];});
render();
</script></body></html>"""

def q(sql): return pd.read_sql(sql, con)

pob = q("SELECT ubigeo_inei,nivel,nombre,departamento,provincia,pob,hombres,mujeres,urbana,rural FROM poblacion_ubigeo")
den = q("SELECT ubigeo,nivel,n_ipress,medicos,enfermeras,obstetras,odontologos,camas,d_medicos,d_enfermeras,d_obstetras,d_camas FROM densidad_salud")
od  = q("SELECT ubigeo,nivel,poblacion pob_total,pob_sis,pob_essalud,pct_oms,brecha_oms,hab_medico,pob_ipress,med_pub,med_ess FROM oferta_demanda")
seg = q("SELECT ubigeo_inei,ubigeo_nivel,poblacion pob_seg,sin_seguro,sis,essalud,privado FROM v_seguro WHERE ubigeo_inei IS NOT NULL")

# viviendas por DD y DDPP (VIV1) y hogares por DD (INDDEM05)
def geo_val(hoja, col, nivel):
    if nivel == "departamento":
        j = "u.nombre_norm=f.etiqueta_norm AND u.nivel='departamento'"; key = "substr(u.ubigeo_inei,1,2)"
    else:
        j = "u.nombre_norm=SUBSTR(f.etiqueta_norm,11) AND u.nivel='provincia'"; key = "substr(u.ubigeo_inei,1,4)"
    cond = "f.etiqueta_norm LIKE 'provincia %'" if nivel == "provincia" else "1=1"
    return q(f"""SELECT {key} k, d.valor v FROM dato d
        JOIN cuadro c ON c.cuadro_id=d.cuadro_id JOIN dim_fila f ON f.fila_id=d.fila_id
        JOIN dim_columna kk ON kk.col_id=d.col_id JOIN dim_ubigeo u ON {j}
        WHERE c.hoja='{hoja}' AND kk.columna='{col}' AND {cond} AND u.ubigeo_inei IS NOT NULL""").groupby("k")["v"].sum()
viv_dd = geo_val("VIV1","Total","departamento"); viv_pp = geo_val("VIV1","Total","provincia")
hog_dd = geo_val("INDDEM05","Total","departamento")

# ---- claves de nivel ----
pob["dd"] = pob["ubigeo_inei"].str[:2]; pob["ddpp"] = pob["ubigeo_inei"].str[:4]

# ================= DEPARTAMENTO (25 estandar, Lima combinada) =================
pd_dep = pob[pob.nivel=="departamento"].groupby("dd").agg(
    pob_censada=("pob","sum"),hombres=("hombres","sum"),mujeres=("mujeres","sum"),
    urbana=("urbana","sum"),rural=("rural","sum")).reset_index()
DEPNOM={"01":"Amazonas","02":"Áncash","03":"Apurímac","04":"Arequipa","05":"Ayacucho","06":"Cajamarca",
 "07":"Callao","08":"Cusco","09":"Huancavelica","10":"Huánuco","11":"Ica","12":"Junín","13":"La Libertad",
 "14":"Lambayeque","15":"Lima","16":"Loreto","17":"Madre de Dios","18":"Moquegua","19":"Pasco","20":"Piura",
 "21":"Puno","22":"San Martín","23":"Tacna","24":"Tumbes","25":"Ucayali"}
pd_dep["departamento"]=pd_dep["dd"].map(DEPNOM)
d1=den[den.nivel=="departamento"].rename(columns={"ubigeo":"dd"})
o1=od[od.nivel=="departamento"].rename(columns={"ubigeo":"dd"})
# seguro por DD (sumar Lima Metro+Region)
seg_d=seg[seg.ubigeo_nivel=="departamento"].copy(); seg_d["dd"]=seg_d["ubigeo_inei"].str[:2]
seg_d=seg_d.groupby("dd").agg(sis=("sis","sum"),essalud=("essalud","sum"),sin_seguro=("sin_seguro","sum")).reset_index()
dep=pd_dep.merge(o1[["dd","pob_total","pob_sis","pob_essalud","pct_oms","brecha_oms","hab_medico","pob_ipress","med_pub","med_ess"]],on="dd",how="left")
dep=dep.merge(d1[["dd","n_ipress","medicos","enfermeras","obstetras","odontologos","camas","d_medicos","d_enfermeras","d_obstetras"]],on="dd",how="left")
dep=dep.merge(seg_d,on="dd",how="left")
dep["viviendas"]=dep["dd"].map(viv_dd); dep["hogares"]=dep["dd"].map(hog_dd)
dep["ubigeo"]=dep["dd"]+"0000"
dep=dep.drop(columns=["dd"]).sort_values("departamento")

# ================= PROVINCIA (194 + Lima ciudad + Callao) =================
prov=pob[pob.nivel=="provincia"][["ubigeo_inei","departamento","provincia","pob","hombres","mujeres","urbana","rural"]].copy()
prov["ddpp"]=prov["ubigeo_inei"].str[:4]
d2=den[den.nivel=="provincia"].rename(columns={"ubigeo":"ddpp"})
o2=od[od.nivel=="provincia"].rename(columns={"ubigeo":"ddpp"})
seg_p=seg[seg.ubigeo_nivel=="provincia"].copy(); seg_p["ddpp"]=seg_p["ubigeo_inei"].str[:4]
prov=prov.rename(columns={"pob":"pob_censada"})
prov=prov.merge(o2[["ddpp","pob_total","pob_sis","pob_essalud","pct_oms","hab_medico","med_pub","med_ess"]],on="ddpp",how="left")
prov=prov.merge(d2[["ddpp","n_ipress","medicos","enfermeras","obstetras","d_medicos","d_enfermeras"]],on="ddpp",how="left")
prov=prov.merge(seg_p[["ddpp","sis","essalud","sin_seguro"]],on="ddpp",how="left")
prov["viviendas"]=prov["ddpp"].map(viv_pp)
prov=prov.rename(columns={"ubigeo_inei":"ubigeo"}).drop(columns=["ddpp"]).sort_values(["departamento","provincia"])

# ================= DISTRITO (1892) — poblacion + oferta por ubigeo 6 dig =================
dist=pob[pob.nivel=="distrito"][["ubigeo_inei","departamento","provincia","nombre","pob","hombres","mujeres","urbana","rural"]].copy()
dist=dist.rename(columns={"nombre":"distrito","pob":"pob_censada","ubigeo_inei":"ubigeo"})
ip=q("SELECT ubigeo, COUNT(*) ipress FROM ipress GROUP BY ubigeo")
rh=q("SELECT ubigeo, SUM(medicos) medicos, SUM(enfermeras) enfermeras, SUM(obstetras) obstetras, SUM(odontologos) odontologos, SUM(camas) camas FROM salud_rrhh GROUP BY ubigeo")
dist=dist.merge(ip,on="ubigeo",how="left").merge(rh,on="ubigeo",how="left")
for c in ["ipress","medicos","enfermeras","obstetras","odontologos","camas"]: dist[c]=dist[c].fillna(0).astype(int)
dist["med_10k"]=(dist["medicos"]/dist["pob_censada"]*10000).round(1).where(dist["pob_censada"]>0)
dist=dist.sort_values(["departamento","provincia","distrito"])
con.close()

# ---- reordenar columnas: identificadores primero, luego poblacion, salud, oferta ----
ORD=["ubigeo","departamento","provincia","distrito","pob_total","pob_censada","hombres","mujeres",
 "urbana","rural","viviendas","hogares","sis","essalud","sin_seguro","pob_sis","pob_essalud",
 "n_ipress","ipress","medicos","enfermeras","obstetras","odontologos","camas",
 "d_medicos","d_enfermeras","d_obstetras","med_10k","med_pub","med_ess","pct_oms","brecha_oms","hab_medico","pob_ipress"]
def ordena(df): return df[[c for c in ORD if c in df.columns]]
dep,prov,dist=ordena(dep),ordena(prov),ordena(dist)

# ---- redondeos y exportar CSV ----
def clean(df):
    for c in df.columns:
        if df[c].dtype=="float64": df[c]=df[c].round(1)
    return df
dep,prov,dist=clean(dep),clean(prov),clean(dist)
dep.to_csv(os.path.join(OUT,"departamentos.csv"),index=False,encoding="utf-8-sig")
prov.to_csv(os.path.join(OUT,"provincias.csv"),index=False,encoding="utf-8-sig")
dist.to_csv(os.path.join(OUT,"distritos.csv"),index=False,encoding="utf-8-sig")

# etiquetas legibles de columnas
LBL={"ubigeo":"UBIGEO","departamento":"Departamento","provincia":"Provincia","distrito":"Distrito",
 "pob_total":"Pob. total","pob_censada":"Pob. censada","hombres":"Hombres","mujeres":"Mujeres",
 "urbana":"Urbana","rural":"Rural","viviendas":"Viviendas","hogares":"Hogares",
 "sis":"Afil. SIS","essalud":"Afil. EsSalud","sin_seguro":"Sin seguro","pob_sis":"Pob. SIS","pob_essalud":"Pob. EsSalud",
 "n_ipress":"IPRESS","ipress":"IPRESS","medicos":"Médicos","enfermeras":"Enfermeras","obstetras":"Obstetras",
 "odontologos":"Odontólogos","camas":"Camas","d_medicos":"Méd./10k","d_enfermeras":"Enf./10k","d_obstetras":"Obst./10k",
 "med_10k":"Méd./10k","pct_oms":"% umbral OMS","brecha_oms":"Brecha OMS","hab_medico":"Hab./médico",
 "pob_ipress":"Hab./IPRESS","med_pub":"Méd.púb/10k SIS","med_ess":"Méd.EsSalud/10k"}
def payload(df):
    cols=list(df.columns)
    return {"cols":cols,"lbl":[LBL.get(c,c) for c in cols],
            "rows":json.loads(df.where(pd.notnull(df),None).to_json(orient="values"))}
DATA={"departamento":payload(dep),"provincia":payload(prov),"distrito":payload(dist)}

html=TEMPLATE.replace("__DATA__",json.dumps(DATA,ensure_ascii=False))
open(os.path.join(HERE,"tablas.html"),"w",encoding="utf-8").write(html)
print(f"tablas.html + CSV | dep {len(dep)} | prov {len(prov)} | dist {len(dist)}")
