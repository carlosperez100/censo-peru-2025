# -*- coding: utf-8 -*-
"""Genera comparativo.html: densidad de profesionales de salud del Peru vs America Latina,
EE.UU. y otros paises (Banco Mundial / OMS). Marca GEMSES. Autocontenido."""
import json, os
HERE = os.path.dirname(__file__)
DATA = json.load(open(os.path.join(HERE, "..", "ref", "comparativo_internacional.json"), encoding="utf-8"))

ES = {  # nombre EN -> (nombre ES, bandera/emoji, tipo)
 "Cuba":("Cuba","🇨🇺","pais"),"Argentina":("Argentina","🇦🇷","pais"),"Uruguay":("Uruguay","🇺🇾","pais"),
 "Germany":("Alemania","🇩🇪","pais"),"Spain":("España","🇪🇸","pais"),"Paraguay":("Paraguay","🇵🇾","pais"),
 "United States":("Estados Unidos","🇺🇸","pais"),"Chile":("Chile","🇨🇱","pais"),"Canada":("Canadá","🇨🇦","pais"),
 "Costa Rica":("Costa Rica","🇨🇷","pais"),"Mexico":("México","🇲🇽","pais"),"Colombia":("Colombia","🇨🇴","pais"),
 "Brazil":("Brasil","🇧🇷","pais"),"Ecuador":("Ecuador","🇪🇨","pais"),"Panama":("Panamá","🇵🇦","pais"),
 "Bolivia":("Bolivia","🇧🇴","pais"),"Peru":("Perú","🇵🇪","peru"),
 "OECD members":("Promedio OCDE","📊","ref"),"Latin America & Caribbean":("Prom. A. Latina y Caribe","📊","ref"),
 "World":("Promedio mundial","🌎","ref"),
}
rows = []
for en, v in DATA.items():
    nom, ban, tipo = ES.get(en, (en, "", "pais"))
    rows.append({"nom": nom, "ban": ban, "tipo": tipo,
                 "med": v["med10k"], "enf": v.get("enf10k"), "y": v["med_y"]})
js = json.dumps(rows, ensure_ascii=False)

HTML = r"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Perú vs el mundo — profesionales de salud · GEMSES</title>
<meta name="description" content="Densidad de médicos y enfermeras por 10 000 hab: Perú frente a América Latina, EE.UU. y otros países (Banco Mundial/OMS). Modelo GEMSES.">
<style>
:root{--navy:#0a2e5c;--blue:#124a8f;--blue2:#2b76d1;--teal:#12a5a5;--gold:#e0a80d;--ink:#0e1c30;--muted:#5b6b82;--line:#e2e8f0;--bg:#f4f7fb;--card:#fff}
*{box-sizing:border-box}body{margin:0;font-family:'Segoe UI',system-ui,Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.45}
a{color:var(--blue2);text-decoration:none}
header{background:linear-gradient(120deg,var(--navy),var(--blue) 60%,var(--teal));color:#fff;padding:20px 22px}
.brand{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.logo{font-weight:800;letter-spacing:2px;font-size:22px;border:2px solid var(--gold);border-radius:10px;padding:4px 12px;background:rgba(255,255,255,.06)}
.logo b{color:var(--gold)}
.htxt h1{margin:0;font-size:19px}.htxt p{margin:2px 0 0;font-size:13px;opacity:.9}
.wrap{max-width:960px;margin:18px auto;padding:0 16px}
.card{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 1px 3px rgba(10,46,92,.05)}
.tabs{display:flex;gap:8px;margin-bottom:14px}
.tab{border:1px solid var(--line);background:#fff;color:var(--blue);border-radius:999px;padding:7px 15px;font-size:13.5px;font-weight:700;cursor:pointer}
.tab.active{background:var(--navy);color:#fff;border-color:var(--navy)}
.bars{display:flex;flex-direction:column;gap:7px}
.bar{display:grid;grid-template-columns:190px 1fr 58px;align-items:center;gap:10px;font-size:13.5px}
.bar .nm{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.bar .track{background:var(--bg);border-radius:6px;height:22px;overflow:hidden;border:1px solid var(--line)}
.bar .fill{height:100%;border-radius:6px 0 0 6px;background:linear-gradient(90deg,var(--teal),var(--blue));transition:width .4s}
.bar.peru .fill{background:linear-gradient(90deg,var(--gold),#c58c00)}
.bar.peru .nm{font-weight:800;color:var(--navy)}
.bar.ref .fill{background:repeating-linear-gradient(45deg,#9fb2cc,#9fb2cc 6px,#b9c7db 6px,#b9c7db 12px)}
.bar.ref .nm{font-style:italic;color:var(--muted)}
.bar .val{text-align:right;font-weight:700;color:var(--navy);font-variant-numeric:tabular-nums}
.note{font-size:12.5px;color:var(--muted);margin-top:14px;border-top:1px solid var(--line);padding-top:10px}
.kx{display:flex;gap:14px;flex-wrap:wrap;margin:8px 0 2px}
.kx div{background:var(--bg);border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:12.5px}
.kx b{color:var(--navy);font-size:15px;display:block}
footer{max-width:960px;margin:8px auto 30px;padding:0 16px;font-size:12px;color:var(--muted)}
.gem{color:var(--navy);font-weight:700}
</style></head><body>
<header><div class="brand">
  <div class="logo">GEM<b>SES</b></div>
  <div class="htxt"><h1>Perú en el contexto internacional — profesionales de salud</h1>
  <p>Densidad por 10 000 habitantes · Banco Mundial / OMS · <a href="index.html" style="color:#fff;text-decoration:underline">← volver al mapa del censo</a></p></div>
</div></header>
<div class="wrap"><div class="card">
  <div class="tabs"><button class="tab active" data-k="med">Médicos /10k</button><button class="tab" data-k="enf">Enfermeras /10k</button></div>
  <div class="kx" id="kx"></div>
  <div class="bars" id="bars"></div>
  <div class="note" id="note"></div>
</div></div>
<footer>Fuente: <a href="https://data.worldbank.org" target="_blank" rel="noopener">Banco Mundial</a> (indicadores OMS
 SH.MED.PHYS.ZS y SH.MED.NUMW.P3), último año disponible por país. La densidad del Perú en el censo/SUSALUD
 (~19 méd/10k, personal en IPRESS) difiere del dato OMS (16,9, médicos activos a nivel nacional) por metodología.
 Visualización <span class="gem">Modelo GEMSES</span> · Carlos Pérez Pérez.</footer>
<script>
const D=__DATA__; let cur="med";
function render(){
 const rows=D.filter(d=>d[cur]!=null).sort((a,b)=>b[cur]-a[cur]);
 const mx=Math.max(...rows.map(d=>d[cur]));
 document.getElementById("bars").innerHTML=rows.map(d=>{
   const cls=d.tipo==="peru"?"peru":(d.tipo==="ref"?"ref":"");
   return `<div class="bar ${cls}"><span class="nm">${d.ban} ${d.nom}</span>
     <span class="track"><span class="fill" style="width:${Math.max(d[cur]/mx*100,1)}%"></span></span>
     <span class="val">${d[cur].toFixed(1)}</span></div>`;}).join("");
 const pe=D.find(d=>d.tipo==="peru"), wo=D.find(d=>d.nom==="Promedio mundial"), la=D.find(d=>d.nom.startsWith("Prom. A. Latina"));
 const rk=rows.findIndex(d=>d.tipo==="peru")+1;
 document.getElementById("kx").innerHTML=
   `<div><b>${pe[cur].toFixed(1)}</b>Perú (por 10k)</div>
    <div><b>${wo[cur].toFixed(1)}</b>Promedio mundial</div>
    <div><b>${la[cur].toFixed(1)}</b>Prom. A. Latina y Caribe</div>
    <div><b>#${rk} / ${rows.length}</b>posición del Perú</div>`;
 const prof=cur==="med"?"médicos":"enfermeras";
 document.getElementById("note").innerHTML=
   `Perú tiene <b>${pe[cur].toFixed(1)}</b> ${prof} por 10 000 hab: `+
   (pe[cur]<wo[cur]?`por <b>debajo</b> del promedio mundial (${wo[cur].toFixed(1)})`:`por encima del promedio mundial (${wo[cur].toFixed(1)})`)+
   ` y del promedio de América Latina y el Caribe (${la[cur].toFixed(1)}).`;
}
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));b.classList.add("active");cur=b.dataset.k;render();}));
render();
</script></body></html>"""
open(os.path.join(HERE, "comparativo.html"), "w", encoding="utf-8").write(HTML.replace("__DATA__", js))
print("comparativo.html generado |", len(rows), "filas")
