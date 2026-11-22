"""Test navigateur facultatif (Playwright) : rendu hors ligne, curseur bi-temporel, interactions.

Usage : pip install playwright && playwright install chromium
        python3 tests/browser_check.py examples/graphe-exemple.html captures/
Variable CHROME : chemin d'un Chrome déjà installé (facultatif).
"""
import os, sys, json, asyncio
from playwright.async_api import async_playwright
path, out = os.path.abspath(sys.argv[1]), sys.argv[2]
os.makedirs(out, exist_ok=True)
LAUNCH = {"args": ["--no-sandbox"]}
if os.environ.get("CHROME"):
    LAUNCH["executable_path"] = os.environ["CHROME"]

VIS = """()=>{const o={};d3.selectAll('#canvas path.edge').each(function(l){if(l.id==='L04'||l.id==='L05')o[l.id]=this.style.display!=='none'});
 d3.selectAll('#canvas g.node').each(function(d){if(d.id==='D02'||d.id==='D03')o[d.id]=this.style.display!=='none'});return o}"""

async def main():
    res = {"requetes_externes": [], "erreurs_js": [], "cas": {}, "interactions": {}}
    async with async_playwright() as p:
        b = await p.chromium.launch(**LAUNCH)
        for name, w, h, scheme in (("desktop", 1440, 1000, "light"), ("mobile", 390, 844, "light"), ("sombre", 1280, 900, "dark")):
            ctx = await b.new_context(viewport={"width": w, "height": h}, accept_downloads=True, offline=True,
                                      color_scheme=scheme, device_scale_factor=2 if name == "mobile" else 1)
            pg = await ctx.new_page()
            pg.on("request", lambda r: res["requetes_externes"].append(r.url) if not r.url.startswith(("file:", "data:", "blob:")) else None)
            pg.on("pageerror", lambda e: res["erreurs_js"].append(f"{name}: {e}"))
            pg.on("console", lambda m: res["erreurs_js"].append(f"{name}: {m.text}") if m.type == "error" else None)
            await pg.goto("file://" + path); await pg.wait_for_timeout(900)
            await pg.screenshot(path=f"{out}/{name}-haut.png")
            await pg.screenshot(path=f"{out}/{name}-complet.png", full_page=True)
            if name == "desktop":
                fonts = await pg.evaluate("document.fonts.check('500 14px \"Plex Sans\"') && document.fonts.check('500 14px \"Plex Mono\"')")
                res["polices_integrees"] = fonts
                async def vis(mode, date):
                    await pg.check(f"input[name=mode][value={mode}]", force=True)
                    await pg.fill("#date", date); await pg.dispatch_event("#date", "change")
                    return await pg.evaluate(VIS)
                res["cas"]["vrai_2026-10-19"] = await vis("vrai", "2026-10-19")
                res["cas"]["vrai_2026-10-21"] = await vis("vrai", "2026-10-21")
                res["cas"]["connu_2026-10-21"] = await vis("connu", "2026-10-21")
                res["cas"]["connu_2026-10-23"] = await vis("connu", "2026-10-23")
                # curseur au clavier
                await pg.check("input[name=mode][value=vrai]", force=True)
                await pg.fill("#date", "2026-10-19"); await pg.dispatch_event("#date", "change")
                await pg.focus("#tb .ph-knob"); await pg.keyboard.press("Shift+ArrowRight")
                res["interactions"]["clavier_frise"] = await pg.input_value("#date")
                res["interactions"]["apres_clavier"] = await pg.evaluate(VIS)
                await pg.fill("#date", "2026-11-22"); await pg.dispatch_event("#date", "change")
                # glisser un nœud : la simulation doit le déplacer puis le relâcher
                box = await pg.locator("#canvas g.node >> nth=3 >> .hit").bounding_box()
                before = await pg.evaluate("d3.selectAll('#canvas g.node').data().map(n=>[n.x,n.y])")
                await pg.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
                await pg.mouse.down(); await pg.mouse.move(box["x"] + 120, box["y"] + 80, steps=8); await pg.mouse.up()
                await pg.wait_for_timeout(500)
                after = await pg.evaluate("d3.selectAll('#canvas g.node').data().map(n=>[n.x,n.y])")
                res["interactions"]["glisser_deplace"] = max(abs(a[0]-b[0])+abs(a[1]-b[1]) for a,b in zip(after,before)) > 20
                # sélection d'un nœud
                await pg.click("#canvas g.node >> nth=0 >> .hit", force=True)
                res["interactions"]["inspecteur"] = (await pg.inner_text("#inspector"))[:120]
                # survol : voisins isolés
                res["interactions"]["noeuds_attenues_selection"] = await pg.evaluate("document.querySelectorAll('#canvas g.node.dim').length")
                # KPI vers onglet du registre
                await pg.click(".kpi >> nth=1")
                res["interactions"]["onglet_apres_kpi"] = await pg.evaluate("document.querySelector('#reg-tabs [aria-selected=true]').textContent")
                # ligne du registre vers le graphe
                await pg.click("#reg-tabs button >> nth=0"); await pg.click("#reg-body tbody tr >> nth=0")
                res["interactions"]["selection_depuis_registre"] = await pg.evaluate("document.querySelector('#inspector h3') && document.querySelector('#inspector h3').textContent")
                async with pg.expect_download() as dl: await pg.click("#b-md")
                res["interactions"]["telechargement"] = (await dl.value).suggested_filename
                await pg.emulate_media(media="print"); await pg.screenshot(path=f"{out}/impression.png", full_page=True); await pg.emulate_media(media="screen")
                # contrastes des textes clés
                res["contrastes"] = await pg.evaluate("""()=>{function lum(c){const m=c.match(/[\\d.]+/g).map(Number).slice(0,3).map(v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)});return .2126*m[0]+.7152*m[1]+.0722*m[2]}
                 function ratio(a,b){const x=lum(a),y=lum(b);return +(((Math.max(x,y)+.05)/(Math.min(x,y)+.05)).toFixed(2))}
                 const bg=getComputedStyle(document.querySelector('.card')).backgroundColor;const o={};
                 [['texte secondaire','.kpi .k-lbl'],['texte tertiaire','.kpi .k-sub'],['ouvert','.st-ouvert'],['proposé','.st-propose'],['fait','.st-fait'],['hypothèse','.st-hyp']].forEach(([n,s])=>{const e=document.querySelector(s);if(e)o[n]=ratio(getComputedStyle(e).color,bg)});return o}""")
            if name == "mobile":
                res["mobile_debordement"] = await pg.evaluate("document.documentElement.scrollWidth > window.innerWidth")
            await ctx.close()
        await b.close()
    print(json.dumps(res, ensure_ascii=False, indent=1))
    ok = not res["erreurs_js"] and not res["requetes_externes"] and res["interactions"].get("glisser_deplace")
    sys.exit(0 if ok else 1)

asyncio.run(main())
