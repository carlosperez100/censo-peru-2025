# -*- coding: utf-8 -*-
"""
Genera un mapa coropletico interactivo del Peru (replica del visor INEI) con marca GEMSES,
alimentado por censo2025.db. Salida autocontenida: index.html (sin dependencias externas).
"""
import sqlite3, json, os, unicodedata

HERE = os.path.dirname(__file__)
DB   = os.path.join(HERE, "..", "censo2025.db")
GEO  = os.path.join(HERE, "peru_dep.geojson")

def norm(s):
    s = "".join(c for c in unicodedata.normalize("NFD", str(s)) if unicodedata.category(c) != "Mn")
    return s.strip().lower()

HTML_TEMPLATE = r"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Censo 2025 · Perú — Modelo GEMSES</title>
<meta name="description" content="Mapa coroplético del Censo Nacional 2025 (INEI) por departamento, con el modelo GEMSES. Datos oficiales, consulta interactiva.">
<style>
:root{
  --navy:#0a2e5c; --blue:#124a8f; --blue2:#2b76d1; --teal:#12a5a5; --gold:#e0a80d;
  --ink:#0e1c30; --muted:#5b6b82; --line:#e2e8f0; --bg:#f4f7fb; --card:#ffffff;
}
*{box-sizing:border-box}
body{margin:0;font-family:'Segoe UI',system-ui,-apple-system,Roboto,Arial,sans-serif;
  color:var(--ink);background:var(--bg);line-height:1.45}
a{color:var(--blue2);text-decoration:none}
header{background:linear-gradient(120deg,var(--navy),var(--blue) 60%,var(--teal));color:#fff;padding:20px 22px}
.brand{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{font-weight:800;letter-spacing:2px;font-size:22px;
  border:2px solid var(--gold);border-radius:10px;padding:4px 12px;background:rgba(255,255,255,.06)}
.logo b{color:var(--gold)}
.htxt h1{margin:0;font-size:20px;font-weight:700}
.htxt p{margin:2px 0 0;font-size:13px;opacity:.85}
.wrap{max-width:1180px;margin:18px auto;padding:0 16px;display:grid;grid-template-columns:1.3fr .9fr;gap:18px}
@media(max-width:900px){.wrap{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px;
  box-shadow:0 1px 3px rgba(10,46,92,.05)}
.controls{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:12px}
.ind{border:1px solid var(--line);background:#fff;color:var(--blue);border-radius:999px;
  padding:7px 13px;font-size:13px;font-weight:600;cursor:pointer;transition:.15s}
.ind:hover{border-color:var(--blue2)}
.ind.active{background:var(--navy);color:#fff;border-color:var(--navy)}
svg#map{width:100%;height:auto;display:block}
path.dep{stroke:#fff;stroke-width:.8;cursor:pointer;transition:opacity .1s}
path.dep:hover{opacity:.82;stroke:var(--gold);stroke-width:1.6}
path.dep.sel{stroke:var(--gold);stroke-width:2}
.legend{display:flex;align-items:center;gap:10px;margin-top:6px;font-size:12px;color:var(--muted)}
.ramp{height:12px;flex:1;border-radius:6px;border:1px solid var(--line)}
.tip{position:fixed;pointer-events:none;background:var(--navy);color:#fff;padding:7px 10px;border-radius:8px;
  font-size:12.5px;opacity:0;transform:translateY(-4px);transition:.08s;z-index:9;max-width:220px}
.tip b{color:var(--gold)}
h2{font-size:15px;margin:0 0 10px;color:var(--navy)}
.detail .dep{font-size:18px;font-weight:800;color:var(--navy);margin-bottom:8px}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.kpi{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:9px 11px}
.kpi .v{font-size:17px;font-weight:800;color:var(--blue)}
.kpi .l{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.4px}
ol.rank{list-style:none;margin:0;padding:0;counter-reset:r}
ol.rank li{counter-increment:r;display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px dashed var(--line);font-size:13.5px}
ol.rank li::before{content:counter(r);background:var(--navy);color:#fff;font-size:11px;font-weight:700;
  width:20px;height:20px;border-radius:50%;display:grid;place-items:center;flex:none}
ol.rank .bar{flex:1;height:8px;background:var(--bg);border-radius:5px;overflow:hidden}
ol.rank .bar>i{display:block;height:100%;background:linear-gradient(90deg,var(--teal),var(--blue))}
ol.rank .val{font-weight:700;color:var(--navy);font-variant-numeric:tabular-nums}
.stat{display:flex;gap:16px;flex-wrap:wrap;margin-top:4px}
.stat div{font-size:12px;color:var(--muted)}
.stat b{display:block;font-size:18px;color:var(--navy)}
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
      <p>Mapa por departamento a partir de datos oficiales del INEI · Población censada: __TOTAL__ habitantes</p>
    </div>
  </div>
</header>

<div class="wrap">
  <div class="card">
    <div class="controls" id="controls"></div>
    <svg id="map" viewBox="0 0 __W__ __H__" role="img" aria-label="Mapa del Perú por departamento"></svg>
    <div class="legend"><span id="lmin">0</span><div class="ramp" id="ramp"></div><span id="lmax">—</span></div>
  </div>

  <div>
    <div class="card detail" style="margin-bottom:16px">
      <h2>Departamento</h2>
      <div class="dep" id="dName">Perú (nacional)</div>
      <div class="kpis" id="dKpis"></div>
      <div class="stat" style="margin-top:12px">
        <div><b id="sPob">—</b>población</div>
        <div><b id="sUrb">—</b>% urbana</div>
        <div><b id="sMuj">—</b>% mujeres</div>
      </div>
    </div>
    <div class="card">
      <h2 id="rankTitle">Ranking</h2>
      <ol class="rank" id="rank"></ol>
    </div>
  </div>
</div>

<div class="tip" id="tip"></div>

<footer>
  Fuente: <a href="https://censos2025.inei.gob.pe" target="_blank" rel="noopener">INEI — Censos Nacionales 2025</a>,
  XIII de Población, VIII de Vivienda y IV de Comunidades Indígenas · Tabulados de Población.
  Visualización <span class="gem">Modelo GEMSES</span> — Gestión Moderna de los Servicios de Salud ·
  Carlos Pérez Pérez. Datos procesados a base relacional única (censo2025.db).
</footer>

<script>
const DATA = __DATA__;
const INDS = [
  {k:"pob",   t:"Población",              fmt:v=>v.toLocaleString("es-PE"), suf:""},
  {k:"den",   t:"Densidad (hab/km²)",     fmt:v=>v.toLocaleString("es-PE"), suf:""},
  {k:"pmuj",  t:"% Mujeres",              fmt:v=>v.toFixed(1),              suf:"%"},
  {k:"purb",  t:"% Urbana",               fmt:v=>v.toFixed(1),              suf:"%"},
  {k:"prur",  t:"% Rural",                fmt:v=>v.toFixed(1),              suf:"%"},
  {k:"imasc", t:"Índice masculinidad",    fmt:v=>v.toFixed(1),             suf:""},
];
let cur = INDS[0];

// rampa secuencial marca GEMSES: claro -> navy
function lerp(a,b,t){return a+(b-a)*t}
function hex(c){return c.toString(16).padStart(2,"0")}
function color(t){ // t 0..1
  const c0=[234,241,251], c1=[10,46,92];   // #eaf1fb -> var(--navy)
  return "#"+hex(Math.round(lerp(c0[0],c1[0],t)))+hex(Math.round(lerp(c0[1],c1[1],t)))+hex(Math.round(lerp(c0[2],c1[2],t)));
}
const svg=document.getElementById("map"), tip=document.getElementById("tip");
let selected=null;

function render(){
  const vals=DATA.map(d=>d[cur.k]);
  const mn=Math.min(...vals), mx=Math.max(...vals);
  svg.innerHTML="";
  DATA.forEach(d=>{
    const t=(mx>mn)?(d[cur.k]-mn)/(mx-mn):0;
    const p=document.createElementNS("http://www.w3.org/2000/svg","path");
    p.setAttribute("d",d.d); p.setAttribute("class","dep"+(selected===d?" sel":""));
    p.setAttribute("fill",color(t));
    p.addEventListener("mousemove",e=>{
      tip.style.opacity=1; tip.style.left=(e.clientX+14)+"px"; tip.style.top=(e.clientY-10)+"px";
      tip.innerHTML=`<b>${d.dep}</b><br>${cur.t}: ${cur.fmt(d[cur.k])}${cur.suf}`;
    });
    p.addEventListener("mouseleave",()=>tip.style.opacity=0);
    p.addEventListener("click",()=>{selected=d; render(); detail(d);});
    svg.appendChild(p);
  });
  document.getElementById("ramp").style.background=`linear-gradient(90deg,${color(0)},${color(.5)},${color(1)})`;
  document.getElementById("lmin").textContent=cur.fmt(mn)+cur.suf;
  document.getElementById("lmax").textContent=cur.fmt(mx)+cur.suf;
  ranking(mn,mx);
}
function ranking(mn,mx){
  const rows=[...DATA].sort((a,b)=>b[cur.k]-a[cur.k]).slice(0,12);
  document.getElementById("rankTitle").textContent="Ranking · "+cur.t;
  document.getElementById("rank").innerHTML=rows.map(d=>{
    const w=(mx>mn)?Math.round((d[cur.k]-mn)/(mx-mn)*100):0;
    return `<li><span style="flex:none;min-width:120px">${d.dep}</span>
      <span class="bar"><i style="width:${Math.max(w,4)}%"></i></span>
      <span class="val">${cur.fmt(d[cur.k])}${cur.suf}</span></li>`;
  }).join("");
}
function detail(d){
  document.getElementById("dName").textContent=d.dep;
  const k=[["Población",d.pob.toLocaleString("es-PE")],["Hombres",d.hom.toLocaleString("es-PE")],
    ["Mujeres",d.muj.toLocaleString("es-PE")],["Densidad",d.den.toLocaleString("es-PE")+" hab/km²"],
    ["% Urbana",d.purb+"%"],["% Rural",d.prur+"%"]];
  document.getElementById("dKpis").innerHTML=k.map(x=>`<div class="kpi"><div class="v">${x[1]}</div><div class="l">${x[0]}</div></div>`).join("");
  document.getElementById("sPob").textContent=d.pob.toLocaleString("es-PE");
  document.getElementById("sUrb").textContent=d.purb+"%";
  document.getElementById("sMuj").textContent=d.pmuj+"%";
}
// controles
document.getElementById("controls").innerHTML=INDS.map((i,ix)=>
  `<button class="ind${ix===0?' active':''}" data-k="${i.k}">${i.t}</button>`).join("");
document.querySelectorAll(".ind").forEach(b=>b.addEventListener("click",()=>{
  document.querySelectorAll(".ind").forEach(x=>x.classList.remove("active"));
  b.classList.add("active"); cur=INDS.find(i=>i.k===b.dataset.k); render();
}));
render();
// detalle inicial: departamento mas poblado
detail([...DATA].sort((a,b)=>b.pob-a.pob)[0]);
</script>
</body>
</html>
"""

# ------------------------------------------------------------ 1) datos por departamento
con = sqlite3.connect(DB); cx = con.cursor()
COLS = {"Total":"pob", "Población | Hombre":"hom", "Población | Mujer":"muj",
        "Total #2":"urb", "Total #3":"rur"}
# valor por unidad de primer nivel (26) y columna
raw = {}
q = """SELECT u.nombre, k.columna, d.valor
       FROM dato d
       JOIN cuadro c   ON c.cuadro_id=d.cuadro_id
       JOIN dim_fila f ON f.fila_id=d.fila_id
       JOIN dim_columna k ON k.col_id=d.col_id
       JOIN dim_ubigeo u  ON u.nombre_norm = f.etiqueta_norm AND u.nivel='departamento'
       WHERE c.hoja='INDDEM01' AND k.columna IN ('Total','Población | Hombre','Población | Mujer','Total #2','Total #3')"""
for nombre, col, val in cx.execute(q):
    raw.setdefault(norm(nombre), {})[COLS[col]] = val
con.close()

# mapear a los 25 departamentos del GeoJSON (Lima = Lima Metropolitana + Region Lima)
def dep_data(nombdep):
    n = norm(nombdep)
    if n == "callao":
        keys = ["prov. const. del callao"]
    elif n == "lima":
        keys = ["lima metropolitana", "region lima"]
    else:
        keys = [k for k in raw if k == n]
    agg = {}
    for k in keys:
        for m, v in raw.get(k, {}).items():
            agg[m] = agg.get(m, 0) + v
    return agg

# ------------------------------------------------------------ 2) geometria -> SVG
geo = json.load(open(GEO, encoding="utf-8"))
# bounding box
xs, ys = [], []
def walk(coords, depth):
    if depth == 0:
        xs.append(coords[0]); ys.append(coords[1])
    else:
        for c in coords: walk(c, depth-1)
for f in geo["features"]:
    g = f["geometry"]
    walk(g["coordinates"], {"Polygon":2, "MultiPolygon":3}[g["type"]])
minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
W, H = 720, 940
pad = 20
sx = (W - 2*pad) / (maxx - minx)
sy = (H - 2*pad) / (maxy - miny)
s = min(sx, sy)
ox = pad + ((W - 2*pad) - s*(maxx-minx))/2
oy = pad + ((H - 2*pad) - s*(maxy-miny))/2
def px(lon, lat):
    return (ox + (lon-minx)*s, oy + (maxy-lat)*s)   # y invertida

def ring_to_path(ring):
    d = ""
    for i, (lon, lat) in enumerate(ring):
        x, y = px(lon, lat)
        d += ("M" if i == 0 else "L") + f"{x:.1f},{y:.1f}"
    return d + "Z"

feats = []
for f in geo["features"]:
    nombdep = f["properties"]["NOMBDEP"]
    ha = f["properties"].get("HECTARES") or 0
    g = f["geometry"]; polys = g["coordinates"] if g["type"]=="MultiPolygon" else [g["coordinates"]]
    d = "".join(ring_to_path(ring) for poly in polys for ring in poly)
    dd = dep_data(nombdep)
    pob = dd.get("pob", 0); hom = dd.get("hom", 0); muj = dd.get("muj", 0)
    urb = dd.get("urb", 0); rur = dd.get("rur", 0)
    km2 = ha/100.0 if ha else 0
    feats.append({
        "dep": nombdep.title(), "d": d,
        "pob": pob, "hom": hom, "muj": muj, "urb": urb, "rur": rur,
        "km2": round(km2), "den": round(pob/km2, 1) if km2 else 0,
        "pmuj": round(muj/pob*100, 1) if pob else 0,
        "purb": round(urb/pob*100, 1) if pob else 0,
        "prur": round(rur/pob*100, 1) if pob else 0,
        "imasc": round(hom/muj*100, 1) if muj else 0,
    })

total_pob = sum(f["pob"] for f in feats)
data_js = json.dumps(feats, ensure_ascii=False)

# ------------------------------------------------------------ 3) HTML (marca GEMSES)
html = HTML_TEMPLATE.replace("__DATA__", data_js)\
                    .replace("__W__", str(W)).replace("__H__", str(H))\
                    .replace("__TOTAL__", f"{int(total_pob):,}".replace(",", " "))
open(os.path.join(HERE, "index.html"), "w", encoding="utf-8").write(html)
print("index.html generado |", len(feats), "departamentos | poblacion total:", f"{total_pob:,}")
