# -*- coding: utf-8 -*-
"""
Mapa coropletico interactivo del Peru (replica del visor INEI) con marca GEMSES,
alimentado por censo2025.db. Dos niveles con DRILL-DOWN (departamento -> provincia) y
capa de AFILIACION A SEGURO DE SALUD (SIS, EsSalud, privado, sin seguro).
Salida autocontenida: index.html (sin dependencias externas).
"""
import sqlite3, json, os, unicodedata

HERE = os.path.dirname(__file__)
DB   = os.path.join(HERE, "..", "censo2025.db")
GEO_DEP  = os.path.join(HERE, "peru_dep.geojson")
GEO_PROV = os.path.join(HERE, "peru_prov.geojson")

def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    return s.strip().lower()

HTML_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Censo 2025 · Perú — Modelo GEMSES</title>
<meta name="description" content="Mapa del Censo 2025 (INEI): población y afiliación a seguro de salud (SIS, EsSalud, privado) por departamento y provincia. Modelo GEMSES.">
<style>
:root{--navy:#0a2e5c;--blue:#124a8f;--blue2:#2b76d1;--teal:#12a5a5;--gold:#e0a80d;
 --ink:#0e1c30;--muted:#5b6b82;--line:#e2e8f0;--bg:#f4f7fb;--card:#fff}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.45}
a{color:var(--blue2);text-decoration:none}
header{background:linear-gradient(120deg,var(--navy),var(--blue) 58%,var(--teal));color:#fff;padding:18px 22px}
.brand{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{font-weight:800;letter-spacing:2px;font-size:22px;border:2px solid var(--gold);border-radius:10px;padding:4px 12px;background:rgba(255,255,255,.06)}
.logo b{color:var(--gold)}
.htxt h1{margin:0;font-size:19px;font-weight:700}
.htxt p{margin:2px 0 0;font-size:13px;opacity:.9}
.hsum{display:flex;gap:18px;margin-top:10px;flex-wrap:wrap}
.hsum div{font-size:12px;opacity:.92}
.hsum b{display:block;font-size:16px;color:var(--gold)}
.wrap{max-width:1180px;margin:16px auto;padding:0 16px;display:grid;grid-template-columns:1.3fr .9fr;gap:18px}
@media(max-width:900px){.wrap{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;box-shadow:0 1px 3px rgba(10,46,92,.05)}
.grp{font-size:11px;text-transform:uppercase;letter-spacing:.6px;color:var(--muted);margin:2px 0 6px;font-weight:700}
.controls{display:flex;flex-wrap:wrap;gap:7px;margin-bottom:8px}
.ind{border:1px solid var(--line);background:#fff;color:var(--blue);border-radius:999px;padding:6px 12px;font-size:12.5px;font-weight:600;cursor:pointer;transition:.15s}
.ind:hover{border-color:var(--blue2)}
.ind.active{background:var(--navy);color:#fff;border-color:var(--navy)}
.ind.salud.active{background:var(--teal);border-color:var(--teal)}
.bc{display:flex;align-items:center;gap:8px;font-size:13px;margin:10px 0 6px;color:var(--muted)}
.bc button{border:1px solid var(--line);background:#fff;border-radius:8px;padding:3px 9px;font-size:12px;cursor:pointer;color:var(--blue)}
.bc b{color:var(--navy)}
svg#map{width:100%;height:auto;display:block}
path.u{stroke:#fff;stroke-width:.6;cursor:pointer;transition:opacity .1s}
path.u:hover{opacity:.82;stroke:var(--gold);stroke-width:1.4}
.legend{display:flex;align-items:center;gap:10px;margin-top:6px;font-size:12px;color:var(--muted)}
.ramp{height:12px;flex:1;border-radius:6px;border:1px solid var(--line)}
.tip{position:fixed;pointer-events:none;background:var(--navy);color:#fff;padding:7px 10px;border-radius:8px;font-size:12.5px;opacity:0;transition:.08s;z-index:9;max-width:230px}
.tip b{color:var(--gold)}
h2{font-size:15px;margin:0 0 10px;color:var(--navy)}
.detail .nm{font-size:18px;font-weight:800;color:var(--navy)}
.detail .sub{font-size:12px;color:var(--muted);margin-bottom:10px}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.kpi{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:8px 10px}
.kpi .v{font-size:16px;font-weight:800;color:var(--blue)}
.kpi .l{font-size:10.5px;color:var(--muted);text-transform:uppercase;letter-spacing:.3px}
.seg{margin-top:6px}
.seg .row{display:flex;align-items:center;gap:8px;margin:5px 0;font-size:12.5px}
.seg .row span:first-child{min-width:88px;color:var(--ink)}
.seg .bar{flex:1;height:9px;background:var(--bg);border-radius:5px;overflow:hidden}
.seg .bar>i{display:block;height:100%}
.seg .val{font-weight:700;color:var(--navy);min-width:44px;text-align:right;font-variant-numeric:tabular-nums}
ol.rank{list-style:none;margin:0;padding:0;counter-reset:r}
ol.rank li{counter-increment:r;display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px dashed var(--line);font-size:13px;cursor:pointer}
ol.rank li:hover{color:var(--blue2)}
ol.rank li::before{content:counter(r);background:var(--navy);color:#fff;font-size:11px;font-weight:700;width:19px;height:19px;border-radius:50%;display:grid;place-items:center;flex:none}
ol.rank .bar{flex:1;height:8px;background:var(--bg);border-radius:5px;overflow:hidden}
ol.rank .bar>i{display:block;height:100%;background:linear-gradient(90deg,var(--teal),var(--blue))}
ol.rank .val{font-weight:700;color:var(--navy);font-variant-numeric:tabular-nums}
footer{max-width:1180px;margin:8px auto 30px;padding:0 16px;font-size:12px;color:var(--muted)}
footer .gem{color:var(--navy);font-weight:700}
</style>
</head>
<body>
<header>
  <div class="brand">
    <div class="logo">GEM<b>SES</b></div>
    <div class="htxt">
      <h1>Censo Nacional 2025 · Perú — Modelo GEMSES</h1>
      <p>Población y <b>afiliación a seguro de salud</b> por departamento y provincia · datos oficiales del INEI</p>
    </div>
  </div>
  <div class="hsum">
    <div>Población censada<b>__TOTAL__</b></div>
    <div>Afiliados al SIS<b>__SIS__</b></div>
    <div>Afiliados a EsSalud<b>__ESS__</b></div>
    <div>Sin ningún seguro<b>__SIN__</b></div>
  </div>
</header>

<div class="wrap">
  <div class="card">
    <div class="grp">Demografía</div>
    <div class="controls" id="cDemo"></div>
    <div class="grp">Salud — afiliación a seguro</div>
    <div class="controls" id="cSalud"></div>
    <div class="bc" id="bc"></div>
    <svg id="map" viewBox="0 0 __W__ __H__" role="img" aria-label="Mapa del Perú"></svg>
    <div class="legend"><span id="lmin">0</span><div class="ramp" id="ramp"></div><span id="lmax">—</span></div>
  </div>
  <div>
    <div class="card detail" style="margin-bottom:16px">
      <h2>Detalle</h2>
      <div class="nm" id="dName">Perú</div>
      <div class="sub" id="dSub">Nivel nacional</div>
      <div class="kpis" id="dKpis"></div>
      <div class="grp">¿Dónde están los afiliados? (% de la población)</div>
      <div class="seg" id="dSeg"></div>
    </div>
    <div class="card">
      <h2 id="rankTitle">Ranking</h2>
      <ol class="rank" id="rank"></ol>
    </div>
  </div>
</div>
<div class="tip" id="tip"></div>
<footer>
  Fuente: <a href="https://censos2025.inei.gob.pe" target="_blank" rel="noopener">INEI — Censos Nacionales 2025</a>
  (Tabulados de Población, cuadros INDDEM01 y SALUD06). La afiliación puede ser múltiple, por eso los
  porcentajes por tipo pueden sumar más de 100%. Visualización <span class="gem">Modelo GEMSES</span> ·
  Carlos Pérez Pérez · base relacional única indexada por UBIGEO (censo2025.db).
</footer>

<script>
const DEPS=__DEPS__, PROVS=__PROVS__;
const DEMO=[
 {k:"pob",t:"Población",fmt:v=>v.toLocaleString("es-PE"),suf:""},
 {k:"den",t:"Densidad",fmt:v=>v.toLocaleString("es-PE"),suf:" hab/km²"},
 {k:"purb",t:"% Urbana",fmt:v=>v.toFixed(1),suf:"%"},
 {k:"pmuj",t:"% Mujeres",fmt:v=>v.toFixed(1),suf:"%"},
];
const SALUD=[
 {k:"pcon",t:"% Con seguro",fmt:v=>v.toFixed(1),suf:"%",sal:1},
 {k:"psis",t:"% SIS",fmt:v=>v.toFixed(1),suf:"%",sal:1},
 {k:"pess",t:"% EsSalud",fmt:v=>v.toFixed(1),suf:"%",sal:1},
 {k:"psin",t:"% Sin seguro",fmt:v=>v.toFixed(1),suf:"%",sal:1},
 {k:"ppri",t:"% Privado",fmt:v=>v.toFixed(1),suf:"%",sal:1},
];
const ALL=[...DEMO,...SALUD];
let cur=DEMO[0], level="nac";  // "nac" o codigo de depto

function lerp(a,b,t){return a+(b-a)*t}
function hx(c){return c.toString(16).padStart(2,"0")}
function color(t,salud){const c0=salud?[224,244,244]:[234,241,251], c1=salud?[10,84,84]:[10,46,92];
 return "#"+hx(Math.round(lerp(c0[0],c1[0],t)))+hx(Math.round(lerp(c0[1],c1[1],t)))+hx(Math.round(lerp(c0[2],c1[2],t)));}
const svg=document.getElementById("map"), tip=document.getElementById("tip");
let selected=null;

function dataset(){ return level==="nac" ? DEPS : PROVS.filter(p=>p.depcod===level); }
function nameOf(u){ return level==="nac"? u.dep : u.prov; }

function render(){
 const ds=dataset(), vals=ds.map(d=>d[cur.k]).filter(v=>v!=null&&!isNaN(v));
 const mn=Math.min(...vals), mx=Math.max(...vals), sal=!!cur.sal;
 // viewBox: nacional o bbox del departamento
 if(level==="nac"){ svg.setAttribute("viewBox","0 0 __W__ __H__"); }
 else{ const dp=DEPS.find(d=>d.cod===level); if(dp&&dp.vb) svg.setAttribute("viewBox",dp.vb.join(" ")); }
 svg.innerHTML="";
 ds.forEach(d=>{
   const raw=d[cur.k], t=(mx>mn&&raw!=null)?(raw-mn)/(mx-mn):0;
   const p=document.createElementNS("http://www.w3.org/2000/svg","path");
   p.setAttribute("d",d.d); p.setAttribute("class","u");
   p.setAttribute("fill", raw==null?"#dfe6f0":color(t,sal));
   p.addEventListener("mousemove",e=>{tip.style.opacity=1;tip.style.left=(e.clientX+14)+"px";tip.style.top=(e.clientY-8)+"px";
     tip.innerHTML=`<b>${nameOf(d)}</b><br>${cur.t}: ${raw==null?"s/d":cur.fmt(raw)+cur.suf}`;});
   p.addEventListener("mouseleave",()=>tip.style.opacity=0);
   p.addEventListener("click",()=>{ if(level==="nac"){ drill(d.cod); } else { selected=d; detail(d);} });
   svg.appendChild(p);
 });
 document.getElementById("ramp").style.background=`linear-gradient(90deg,${color(0,sal)},${color(.5,sal)},${color(1,sal)})`;
 document.getElementById("lmin").textContent=isFinite(mn)?cur.fmt(mn)+cur.suf:"—";
 document.getElementById("lmax").textContent=isFinite(mx)?cur.fmt(mx)+cur.suf:"—";
 ranking(ds,mn,mx); crumbs();
}
function ranking(ds,mn,mx){
 const rows=[...ds].filter(d=>d[cur.k]!=null).sort((a,b)=>b[cur.k]-a[cur.k]).slice(0,12);
 document.getElementById("rankTitle").textContent=(level==="nac"?"Departamentos":"Provincias")+" · "+cur.t;
 document.getElementById("rank").innerHTML=rows.map(d=>{
   const w=(mx>mn)?Math.round((d[cur.k]-mn)/(mx-mn)*100):0;
   return `<li data-nm="${nameOf(d)}"><span style="flex:none;min-width:120px">${nameOf(d)}</span>
     <span class="bar"><i style="width:${Math.max(w,4)}%"></i></span>
     <span class="val">${cur.fmt(d[cur.k])}${cur.suf}</span></li>`;}).join("");
 document.querySelectorAll("#rank li").forEach(li=>li.addEventListener("click",()=>{
   const u=ds.find(d=>nameOf(d)===li.dataset.nm); if(u) detail(u);}));
}
function detail(d){
 selected=d;
 const esProv = d.prov!==undefined;
 document.getElementById("dName").textContent=esProv?d.prov:d.dep;
 document.getElementById("dSub").textContent=esProv?("Provincia · "+d.dep):(d.dep==="Perú"?"Nivel nacional":"Departamento");
 const kp=[["Población",d.pob.toLocaleString("es-PE")],["Con seguro",d.pcon+"%"],
   ["Densidad",d.den.toLocaleString("es-PE")+" hab/km²"],["Sin seguro",d.psin+"%"]];
 document.getElementById("dKpis").innerHTML=kp.map(x=>`<div class="kpi"><div class="v">${x[1]}</div><div class="l">${x[0]}</div></div>`).join("");
 const segs=[["SIS",d.psis,"#12a5a5"],["EsSalud",d.pess,"#124a8f"],["Privado",d.ppri,"#e0a80d"],["Sin seguro",d.psin,"#c0392b"]];
 const mx=Math.max(...segs.map(s=>s[1]),1);
 document.getElementById("dSeg").innerHTML=segs.map(s=>
   `<div class="row"><span>${s[0]}</span><span class="bar"><i style="width:${Math.round(s[1]/mx*100)}%;background:${s[2]}"></i></span><span class="val">${s[1]}%</span></div>`).join("");
}
function drill(cod){ level=cod; selected=null; render(); const dp=DEPS.find(d=>d.cod===cod); if(dp) detail(dp); }
function crumbs(){
 const bc=document.getElementById("bc");
 if(level==="nac"){ bc.innerHTML="<b>Perú</b> · haz clic en un departamento para ver sus provincias"; }
 else{ const dp=DEPS.find(d=>d.cod===level);
   bc.innerHTML=`<button id="back">← Perú</button> <b>${dp?dp.dep:""}</b> · provincias`;
   document.getElementById("back").addEventListener("click",()=>{level="nac";selected=null;render();detail(nac());}); }
}
function nac(){ return {dep:"Perú",prov:"Perú",pob:__TOTALN__,den:0,pcon:0,psin:0,psis:0,pess:0,ppri:0}; }

// controles
document.getElementById("cDemo").innerHTML=DEMO.map((i,x)=>`<button class="ind${x===0?' active':''}" data-k="${i.k}">${i.t}</button>`).join("");
document.getElementById("cSalud").innerHTML=SALUD.map(i=>`<button class="ind salud" data-k="${i.k}">${i.t}</button>`).join("");
document.querySelectorAll(".ind").forEach(b=>b.addEventListener("click",()=>{
 document.querySelectorAll(".ind").forEach(x=>x.classList.remove("active"));
 b.classList.add("active"); cur=ALL.find(i=>i.k===b.dataset.k); render();}));
render();
detail([...DEPS].sort((a,b)=>b.pob-a.pob)[0]);
</script>
</body>
</html>
"""

con = sqlite3.connect(DB); cx = con.cursor()

# ---------------------------------------------------------------- 1) DATOS
# poblacion/sexo/area por unidad de primer nivel (INDDEM01)
COLS = {"Total": "pob", "Población | Hombre": "hom", "Población | Mujer": "muj",
        "Total #2": "urb", "Total #3": "rur"}
pob_raw = {}
for nombre, col, val in cx.execute("""
    SELECT u.nombre, k.columna, d.valor
    FROM dato d JOIN cuadro c ON c.cuadro_id=d.cuadro_id
                JOIN dim_fila f ON f.fila_id=d.fila_id
                JOIN dim_columna k ON k.col_id=d.col_id
                JOIN dim_ubigeo u ON u.nombre_norm=f.etiqueta_norm AND u.nivel='departamento'
    WHERE c.hoja='INDDEM01' AND k.columna IN ('Total','Población | Hombre','Población | Mujer','Total #2','Total #3')"""):
    pob_raw.setdefault(norm(nombre), {})[COLS[col]] = val

# salud por unidad de PRIMER NIVEL (v_seguro dept-level) — keyed por nombre normalizado
# OJO: filtrar a nivel departamento; si no, provincias homonimas (Piura, Cusco...) sobrescriben.
seg_raw = {}
for row in cx.execute("""SELECT ubigeo_nombre, poblacion, sin_seguro, sis, essalud, ffaa_pnp, privado, otro
                          FROM v_seguro WHERE ubigeo_nivel='departamento'"""):
    seg_raw[norm(row[0])] = dict(pob=row[1] or 0, sin=row[2] or 0, sis=row[3] or 0,
                                 essalud=row[4] or 0, ffaa=row[5] or 0, priv=row[6] or 0, otro=row[7] or 0)

# --- por PROVINCIA (DDPP): poblacion/urb/muj (INDDEM01) + salud (v_seguro)
prov_pob = {}   # ddpp -> {pob,urb,muj}
for inei, col, val in cx.execute("""
    SELECT u.ubigeo_inei, k.columna, d.valor
    FROM dato d JOIN cuadro c ON c.cuadro_id=d.cuadro_id
                JOIN dim_fila f ON f.fila_id=d.fila_id
                JOIN dim_columna k ON k.col_id=d.col_id
                JOIN dim_ubigeo u ON u.nombre_norm=REPLACE(REPLACE(f.etiqueta_norm,'provincia ',''),'distrito ','')
    WHERE c.hoja='INDDEM01' AND u.ubigeo_inei IS NOT NULL
      AND (u.nivel='provincia' OR u.nombre IN ('Lima Metropolitana','Prov. Const. del Callao'))
      AND k.columna IN ('Total','Total #2','Población | Mujer')"""):
    d = inei[:4]
    if d == "0700": d = "0701"
    rec = prov_pob.setdefault(d, {})
    rec["pob" if col == "Total" else ("urb" if col == "Total #2" else "muj")] = val
prov_seg = {}   # ddpp -> salud
for inei, nom, lv, pob, sin, sis, es, ff, pr, ot in cx.execute("""
    SELECT ubigeo_inei, ubigeo_nombre, ubigeo_nivel, poblacion, sin_seguro, sis, essalud, ffaa_pnp, privado, otro
    FROM v_seguro WHERE ubigeo_inei IS NOT NULL"""):
    if not (lv == "provincia" or nom in ("Lima Metropolitana", "Prov. Const. del Callao")):
        continue
    d = inei[:4]
    if d == "0700": d = "0701"
    prov_seg[d] = dict(pob=pob or 0, sin=sin or 0, sis=sis or 0, essalud=es or 0,
                       ffaa=ff or 0, priv=pr or 0, otro=ot or 0)
con.close()

def dep_pob(nombdep):
    n = norm(nombdep)
    keys = ["lima metropolitana", "region lima"] if n == "lima" else \
           ["prov. const. del callao"] if n == "callao" else [n]
    agg = {}
    for k in keys:
        for m, v in pob_raw.get(k, {}).items():
            agg[m] = agg.get(m, 0) + v
    return agg

def dep_seg(nombdep):
    n = norm(nombdep)
    keys = ["lima metropolitana", "region lima"] if n == "lima" else \
           ["prov. const. del callao"] if n == "callao" else [n]
    agg = {}
    for k in keys:
        for m, v in seg_raw.get(k, {}).items():
            agg[m] = agg.get(m, 0) + v
    return agg

def indicadores(pob, hom, muj, urb, rur, km2, seg):
    pobs = pob or (seg.get("pob", 0))
    con_seg = pobs - seg.get("sin", 0)
    return {
        "pob": pobs,
        "den": round(pobs / km2, 1) if km2 else 0,
        "purb": round(urb / pob * 100, 1) if pob else 0,
        "pmuj": round(muj / pob * 100, 1) if pob else 0,
        "pcon": round(con_seg / pobs * 100, 1) if pobs else 0,
        "psin": round(seg.get("sin", 0) / pobs * 100, 1) if pobs else 0,
        "psis": round(seg.get("sis", 0) / pobs * 100, 1) if pobs else 0,
        "pess": round(seg.get("essalud", 0) / pobs * 100, 1) if pobs else 0,
        "ppri": round(seg.get("priv", 0) / pobs * 100, 1) if pobs else 0,
        "hom": hom, "muj": muj, "sis": seg.get("sis", 0), "essalud": seg.get("essalud", 0),
        "sin": seg.get("sin", 0), "priv": seg.get("priv", 0),
    }

# ---------------------------------------------------------------- 2) GEOMETRIA -> SVG
def load(path): return json.load(open(path, encoding="utf-8"))
gdep, gprov = load(GEO_DEP), load(GEO_PROV)

xs, ys = [], []
def walk(coords, depth):
    if depth == 0: xs.append(coords[0]); ys.append(coords[1])
    else:
        for c in coords: walk(c, depth-1)
for f in gdep["features"]:
    gm = f["geometry"]; walk(gm["coordinates"], {"Polygon":2,"MultiPolygon":3}[gm["type"]])
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
W, H, pad = 720, 940, 20
s = min((W-2*pad)/(maxx-minx), (H-2*pad)/(maxy-miny))
ox = pad + ((W-2*pad) - s*(maxx-minx))/2
oy = pad + ((H-2*pad) - s*(maxy-miny))/2
def px(lon, lat): return (ox + (lon-minx)*s, oy + (maxy-lat)*s)

def geom_path(gm):
    polys = gm["coordinates"] if gm["type"] == "MultiPolygon" else [gm["coordinates"]]
    d = ""; bx = [1e9, 1e9, -1e9, -1e9]
    for poly in polys:
        for ring in poly:
            for i, (lon, lat) in enumerate(ring):
                x, y = px(lon, lat)
                bx[0]=min(bx[0],x); bx[1]=min(bx[1],y); bx[2]=max(bx[2],x); bx[3]=max(bx[3],y)
                d += ("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}"
            d += "Z"
    return d, bx

# departamentos
deps = []
for f in gdep["features"]:
    nombdep = f["properties"]["NOMBDEP"]
    ha = f["properties"].get("HECTARES") or 0
    d, bx = geom_path(f["geometry"])
    p = dep_pob(nombdep); sg = dep_seg(nombdep)
    ind = indicadores(p.get("pob",0), p.get("hom",0), p.get("muj",0), p.get("urb",0),
                      p.get("rur",0), ha/100.0 if ha else 0, sg)
    ind.update({"dep": nombdep.title(), "d": d, "cod": norm(nombdep),
                "vb": [round(bx[0]-6,1), round(bx[1]-6,1), round(bx[2]-bx[0]+12,1), round(bx[3]-bx[1]+12,1)]})
    deps.append(ind)

# DD (2 digitos) -> codigo de departamento del geojson (norm del NOMBDEP)
DD2DEP = {"01":"amazonas","02":"ancash","03":"apurimac","04":"arequipa","05":"ayacucho",
 "06":"cajamarca","07":"callao","08":"cusco","09":"huancavelica","10":"huanuco","11":"ica",
 "12":"junin","13":"la libertad","14":"lambayeque","15":"lima","16":"loreto","17":"madre de dios",
 "18":"moquegua","19":"pasco","20":"piura","21":"puno","22":"san martin","23":"tacna",
 "24":"tumbes","25":"ucayali"}

# provincias (departamento derivado del prefijo del codigo, el geojson provincial no trae NOMBDEP)
provs = []
for f in gprov["features"]:
    pr = f["properties"]
    ddpp = pr.get("FIRST_IDPR"); nombprov = pr.get("NOMBPROV", "")
    depcod = DD2DEP.get((ddpp or "")[:2], "")
    ha = pr.get("ha") or pr.get("HECTARES") or 0
    d, bx = geom_path(f["geometry"])
    pp = prov_pob.get(ddpp, {}); sg = prov_seg.get(ddpp, {})
    ind = indicadores(pp.get("pob",0), 0, pp.get("muj",0), pp.get("urb",0), 0,
                      ha/100.0 if ha else 0, sg)
    ind.update({"dep": depcod.title(), "prov": nombprov.title(), "d": d,
                "depcod": depcod, "ubigeo": ddpp})
    provs.append(ind)

total_pob = sum(x["pob"] for x in deps)
sis_nac = sum(x["sis"] for x in deps); ess_nac = sum(x["essalud"] for x in deps)
sin_nac = sum(x["sin"] for x in deps)

html = HTML_TEMPLATE.replace("__DEPS__", json.dumps(deps, ensure_ascii=False))\
                    .replace("__PROVS__", json.dumps(provs, ensure_ascii=False))\
                    .replace("__W__", str(W)).replace("__H__", str(H))\
                    .replace("__TOTALN__", str(int(total_pob)))\
                    .replace("__TOTAL__", f"{int(total_pob):,}".replace(",", " "))\
                    .replace("__SIS__", f"{int(sis_nac):,}".replace(",", " "))\
                    .replace("__ESS__", f"{int(ess_nac):,}".replace(",", " "))\
                    .replace("__SIN__", f"{int(sin_nac):,}".replace(",", " "))
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
print(f"index.html: {len(deps)} departamentos, {len(provs)} provincias | pob {int(total_pob):,}")
