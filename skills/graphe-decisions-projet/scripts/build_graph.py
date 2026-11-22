#!/usr/bin/env python3
"""Génère le graphe de connaissances d'un projet en un seul fichier HTML autonome.

Usage :
  python3 build_graph.py registre.json sortie_dossier/ [--precedent graphe-AAAA-MM-JJ.json]
                         [--date AAAA-MM-JJ] [--projet "Nom"] [--constat "Phrase"]

Entrée : registre.json au format renvoyé par Google Sheets get_values, un objet
  {"Onglet": [[en-têtes], [ligne], ...], ...}. Les onglets attendus sont ceux de la
  skill graphe-decisions-projet (Entités, Liens, Décisions, Faits, Actions,
  Contradictions, Rôles, Sources, À valider, Journal, Snapshots, Config).
  Les noms d'onglets et d'en-têtes sont reconnus sans tenir compte des accents ni
  de la casse ; « date d'effet (valid_at) » et « valid_at » sont équivalents.

Sorties, dans sortie_dossier/ :
  graphe.html   page autonome : aucune ressource externe, s'ouvre hors ligne dans
                n'importe quel navigateur, sans Claude ni compte
  graphe.json   données normalisées (permet le diff au passage suivant et la migration)
  handover.md   handover à la troisième personne

Le script n'écrit rien ailleurs et n'appelle aucun réseau. Il imprime un résumé
JSON sur la sortie standard, avec les alertes d'intégrité (sans bloquer).
"""
import argparse, base64, datetime, hashlib, html, json, os, re, sys, unicodedata

VERSION = "1.2.0"
HERE = os.path.dirname(os.path.abspath(__file__))
D3_PATH = os.path.join(HERE, "vendor", "d3.min.js")

def slug(s):
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode().lower()
    s = s.replace("’", "'")
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")

TABS = {"entites": "entites", "liens": "liens", "decisions": "decisions", "faits": "faits",
        "actions": "actions", "contradictions": "contradictions", "roles": "roles",
        "sources": "sources", "a_valider": "a_valider", "journal": "journal",
        "snapshots": "snapshots", "config": "config", "meta": "config"}

CANON = {"valid_at", "invalid_at", "recorded_at", "expired_at", "repere"}
ALIAS = {
    "date_d_effet": "valid_at", "fin_d_effet": "invalid_at", "consigne_le": "recorded_at",
    "clos_le": "expired_at", "revoir_le": "revoir_le", "valable_jusqu_au_revoir_le": "revoir_le",
    "valable_jusqu_au": "revoir_le", "niveau_de_preuve": "niveau_preuve",
    "remplace_par": "remplace_par", "propose_par": "propose_par", "alternatives_ecartees": "alternatives",
    "prediction_ou_critere_de_succes": "critere_succes", "resultat_observe": "resultat",
    "cree_le": "cree_le", "mis_a_jour_le": "maj_le", "decision_liee": "decision",
    "onglet_cible": "onglet", "ligne_proposee": "ligne", "tranchee_par": "tranchee_par",
    "decideur_legitime": "decideur", "libelle": "libelle", "enonce": "enonce",
}

def header_key(h):
    m = re.match(r"^(.*?)\s*\((.*)\)\s*$", str(h).strip())
    base, inner = (m.group(1), m.group(2)) if m else (str(h), "")
    inner_s, base_s = slug(inner), slug(base)
    if inner_s in CANON:
        return inner_s
    if base_s == "source" and inner_s.startswith("repere"):
        return "repere"
    if base_s == "version_a" or base_s == "version_b":
        return base_s
    return ALIAS.get(base_s, base_s)

def table(rows):
    if not rows:
        return []
    keys = [header_key(h) for h in rows[0]]
    out = []
    for r in rows[1:]:
        r = list(r) + [""] * (len(keys) - len(r))
        d = {}
        for i, k in enumerate(keys):
            if k and k not in d:
                d[k] = str(r[i]).strip()
        if any(d.values()):
            out.append(d)
    return out

def norm_status(s):
    s = slug(s)
    for key, val in (("decid", "decide"), ("fait", "fait"), ("propos", "propose"), ("hyp", "hyp"),
                     ("ouvert", "ouvert"), ("a_tranch", "ouvert"), ("remplac", "remplace"),
                     ("abandon", "remplace"), ("perim", "perime"), ("actif", "actif"),
                     ("contest", "conteste"), ("clos", "clos"), ("fusion", "fusionne")):
        if s.startswith(key):
            return val
    return s

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATE_FIELDS = ("valid_at", "invalid_at", "recorded_at", "expired_at", "revoir_le", "echeance",
               "cree_le", "maj_le", "date")

def checks(R):
    w = []
    ent = {e.get("id") for e in R["entites"] if e.get("id")}
    for name in ("entites", "liens", "decisions", "faits", "actions", "contradictions"):
        seen = set()
        for r in R[name]:
            i = r.get("id", "")
            if not i:
                w.append(f"{name} : ligne sans identifiant")
            elif i in seen:
                w.append(f"{name} {i} : identifiant en double")
            seen.add(i)
            for f in DATE_FIELDS:
                v = r.get(f, "")
                if v and not DATE_RE.match(v):
                    w.append(f"{name} {i} : {f} « {v} » n'est pas au format AAAA-MM-JJ")
            if r.get("valid_at") and r.get("invalid_at") and r["invalid_at"] < r["valid_at"]:
                w.append(f"{name} {i} : invalid_at antérieur à valid_at")
            if r.get("recorded_at") and r.get("expired_at") and r["expired_at"] < r["recorded_at"]:
                w.append(f"{name} {i} : expired_at antérieur à recorded_at")
            if norm_status(r.get("statut", "")) == "remplace" and not r.get("invalid_at") and name != "entites":
                w.append(f"{name} {i} : remplacé sans invalid_at (fin inconnue à noter au Journal)")
    ids = {name: {r.get("id") for r in R[name]} for name in ("liens", "decisions", "faits")}
    for l in R["liens"]:
        for end in ("source", "cible"):
            if l.get(end) and l[end] not in ent:
                w.append(f"liens {l.get('id')} : {end} {l[end]} absente des entités")
        if l.get("remplace_par") and l["remplace_par"] not in ids["liens"]:
            w.append(f"liens {l.get('id')} : remplace_par {l['remplace_par']} introuvable")
    for d in R["decisions"]:
        st = norm_status(d.get("statut", ""))
        if st == "decide" and (not d.get("decideur") or not d.get("preuve")):
            w.append(f"décisions {d.get('id')} : décidé sans décideur ou sans preuve")
        if st == "decide" and not d.get("valid_at"):
            w.append(f"décisions {d.get('id')} : décidé sans valid_at")
        for e in re.split(r"[,;\s]+", d.get("entites", "")):
            if e and e not in ent:
                w.append(f"décisions {d.get('id')} : entité {e} absente")
        if d.get("remplace_par") and d["remplace_par"] not in ids["decisions"]:
            w.append(f"décisions {d.get('id')} : remplace_par {d['remplace_par']} introuvable")
    linked = {l.get("source") for l in R["liens"]} | {l.get("cible") for l in R["liens"]}
    for d in R["decisions"]:
        linked |= set(re.split(r"[,;\s]+", d.get("entites", "")))
    for e in R["entites"]:
        if e.get("id") and e["id"] not in linked and norm_status(e.get("statut", "")) not in ("fusionne", "clos"):
            w.append(f"entités {e['id']} : nœud isolé")
    return w

def diff(cur, prev):
    if not prev:
        return None
    out = {"precedent": prev.get("meta", {}).get("registre_lu_le", ""), "items": []}
    for name, label in (("decisions", "Décision"), ("faits", "Fait"), ("contradictions", "Contradiction"),
                        ("actions", "Action"), ("entites", "Entité"), ("liens", "Lien")):
        old = {r.get("id"): r for r in prev.get(name, [])}
        for r in cur[name]:
            o = old.get(r.get("id"))
            txt = r.get("enonce") or r.get("libelle") or r.get("sujet") or r.get("action") or r.get("relation") or ""
            if o is None:
                out["items"].append({"type": "nouveau", "onglet": label, "id": r.get("id"), "texte": txt,
                                     "statut": r.get("statut", "")})
            elif o.get("statut") != r.get("statut") or o.get("invalid_at") != r.get("invalid_at"):
                out["items"].append({"type": "modifie", "onglet": label, "id": r.get("id"), "texte": txt,
                                     "avant": o.get("statut", ""), "statut": r.get("statut", "")})
    return out

def handover(D):
    m = D["meta"]
    L = [f"# Handover : {m['projet']}", "",
         f"Généré le {m['genere_le']} à partir du registre lu le {m['registre_lu_le']}.", "",
         "## Comment lire", "",
         "Ne présenter comme décidé que ce qui porte le statut « décidé ». Niveaux de preuve : primaire "
         "(parole ou écrit du décideur ou de la source), rapporté (rapporté par un tiers), synthèse "
         "(résumé de LLM ou de tiers). Dates : valid_at et invalid_at bornent la période où un élément "
         "est vrai ; recorded_at et expired_at bornent la période où le registre l'a tenu pour vrai.", ""]
    if m.get("objectif"):
        L += ["## Programme", "", m["objectif"], ""]
    if D.get("diff") and D["diff"]["items"]:
        L += ["## Ce qui a changé depuis le " + D["diff"]["precedent"], ""]
        L += [f"- {i['onglet']} {i['id']} ({i['type']}) : {i['texte']} — {i.get('avant', '') + ' → ' if i.get('avant') else ''}{i['statut']}" for i in D["diff"]["items"]]
        L.append("")
    blk = [e for e in D["entites"] if slug(e.get("bloquant", "")) in ("oui", "yes", "true", "1")]
    L += ["## Ce qui bloque", ""] + ([f"- {e['id']} {e.get('libelle', '')} : {e.get('fiche', '')}" for e in blk] or ["- Rien n'est marqué bloquant."]) + [""]
    if D["contradictions"]:
        L += ["## Contradictions", ""] + [f"- {c.get('id')} {c.get('sujet', '')} ({c.get('statut', '')}) : A = {c.get('version_a', '')} ; B = {c.get('version_b', '')}" for c in D["contradictions"]] + [""]
    L += ["## Décisions", ""]
    for d in D["decisions"]:
        bits = [f"{d.get('id')} [{d.get('statut', '')}] {d.get('enonce', '')}"]
        for k, lab in (("decideur", "décideur"), ("valid_at", "effet"), ("invalid_at", "fin"), ("niveau_preuve", "preuve"),
                       ("preuve", "source"), ("remplace_par", "remplacée par")):
            if d.get(k):
                bits.append(f"{lab} : {d[k]}")
        L.append("- " + " ; ".join(bits))
    L.append("")
    act = [f for f in D["faits"] if norm_status(f.get("statut", "")) in ("actif", "")]
    if act:
        L += ["## Faits actifs", ""] + [f"- {f.get('id')} {f.get('enonce', '')} ({f.get('niveau_preuve', '')}, {f.get('valid_at', 'date inconnue')})" for f in act] + [""]
    old = [r for r in D["faits"] + D["liens"] if norm_status(r.get("statut", "")) in ("perime", "remplace")]
    if old:
        L += ["## Périmé et remplacé", ""] + [f"- {r.get('id')} {r.get('enonce') or r.get('relation', '')} : {r.get('statut')}" for r in old] + [""]
    L += ["## Fiches", ""] + [f"- {e.get('id')} {e.get('libelle', '')} ({e.get('type', '')}) : {e.get('fiche', '')}" for e in D["entites"]] + [""]
    if D["roles"]:
        L += ["## Rôles", ""] + [f"- {r.get('domaine', '')} : {r.get('decideur', '')}" for r in D["roles"]] + [""]
    if D["sources"]:
        L += ["## Sources", ""] + [f"- {s.get('repere', '')} {s.get('titre', '')} ({s.get('auteur', '')}, {s.get('date', '')}) {s.get('url', '')}" for s in D["sources"]] + [""]
    L += ["## Limites", "", "Ce handover reflète le registre à sa date de lecture ; il ne remplace pas le registre, qui fait foi.", ""]
    return "\n".join(L)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("registre"); ap.add_argument("sortie")
    ap.add_argument("--precedent"); ap.add_argument("--date"); ap.add_argument("--projet"); ap.add_argument("--constat")
    a = ap.parse_args()
    raw = json.load(open(a.registre, encoding="utf-8"))
    R = {v: [] for v in set(TABS.values())}
    for name, rows in raw.items():
        k = TABS.get(slug(name))
        if k:
            R[k] = table(rows)
    cfg = {}
    for r in R.pop("config"):
        key = r.get("cle") or r.get("parametre") or r.get("champ") or ""
        if key:
            cfg[slug(key)] = r.get("valeur", "")
    today = a.date or datetime.date.today().isoformat()
    meta = {"projet": a.projet or cfg.get("projet") or cfg.get("nom_du_projet") or "Projet",
            "objectif": cfg.get("objectif", ""), "constat": a.constat or cfg.get("constat", ""),
            "centre": cfg.get("centre", ""), "cadence_jours": int(cfg.get("cadence_jours") or 7),
            "registre_url": cfg.get("registre_url", ""), "registre_lu_le": today,
            "genere_le": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"), "generateur": VERSION}
    D = dict(R); D["meta"] = meta
    D["alertes"] = checks(R)
    prev = json.load(open(a.precedent, encoding="utf-8")) if a.precedent else None
    D["diff"] = diff(R, prev)
    md = handover(D)
    D["handover"] = md
    vendor = os.path.join(HERE, "vendor")
    for line in open(os.path.join(vendor, "SHA256SUMS"), encoding="utf-8"):
        digest, name = line.split()
        if hashlib.sha256(open(os.path.join(vendor, name), "rb").read()).hexdigest() != digest:
            sys.exit(f"vendor/{name} ne correspond pas à son empreinte : fichier modifié ou corrompu")
    d3 = open(D3_PATH, encoding="utf-8").read()
    fonts = []
    for fam, wt, fname in (("Plex Sans", 400, "ibm-plex-sans-latin-400-normal"), ("Plex Sans", 500, "ibm-plex-sans-latin-500-normal"),
                           ("Plex Sans", 600, "ibm-plex-sans-latin-600-normal"), ("Plex Mono", 400, "ibm-plex-mono-latin-400-normal"),
                           ("Plex Mono", 500, "ibm-plex-mono-latin-500-normal")):
        b64 = base64.b64encode(open(os.path.join(vendor, "fonts", fname + ".woff2"), "rb").read()).decode()
        fonts.append(f"@font-face{{font-family:'{fam}';font-style:normal;font-weight:{wt};font-display:swap;src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
    tpl = open(os.path.join(HERE, "graphe_template.html"), encoding="utf-8").read()
    blob = json.dumps(D, ensure_ascii=False).replace("</", "<\\/")
    page = (tpl.replace("/*__FONTS__*/", "\n".join(fonts))
               .replace("/*__D3__*/", d3.replace("</script", "<\\/script"))
               .replace("__DATA__", blob)
               .replace("__TITLE__", html.escape(meta["projet"])))
    os.makedirs(a.sortie, exist_ok=True)
    open(os.path.join(a.sortie, "graphe.html"), "w", encoding="utf-8").write(page)
    save = {k: v for k, v in D.items() if k != "handover"}
    open(os.path.join(a.sortie, "graphe.json"), "w", encoding="utf-8").write(json.dumps(save, ensure_ascii=False, indent=1))
    open(os.path.join(a.sortie, "handover.md"), "w", encoding="utf-8").write(md)
    print(json.dumps({"ok": True, "version": VERSION, "registre_lu_le": today,
                      "entites": len(R["entites"]), "liens": len(R["liens"]), "decisions": len(R["decisions"]),
                      "octets_html": len(page.encode("utf-8")), "alertes": D["alertes"]}, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
