"""Tests du générateur, sans dépendance externe : python3 -m unittest discover -s tests -v"""
import json, os, re, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "graphe-decisions-projet", "scripts")
sys.path.insert(0, SCRIPTS)
import build_graph as bg  # noqa: E402

EXAMPLE = os.path.join(ROOT, "examples", "registre-exemple.json")
PREVIOUS = os.path.join(ROOT, "examples", "snapshot-precedent.json")


def run(registre, *args):
    out = tempfile.mkdtemp()
    res = subprocess.run([sys.executable, "-I", os.path.join(SCRIPTS, "build_graph.py"), registre, out, "--date", "2026-11-26", *args],
                         capture_output=True, text=True, check=True)
    return out, json.loads(res.stdout)


def write(obj):
    fd, path = tempfile.mkstemp(suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False)
    return path


class Headers(unittest.TestCase):
    def test_bitemporal_aliases(self):
        self.assertEqual(bg.header_key("date d'effet (valid_at)"), "valid_at")
        self.assertEqual(bg.header_key("Fin d'effet"), "invalid_at")
        self.assertEqual(bg.header_key("consigné le (recorded_at)"), "recorded_at")
        self.assertEqual(bg.header_key("clos le"), "expired_at")

    def test_two_source_columns(self):
        self.assertEqual(bg.header_key("source (Exxx)"), "source")
        self.assertEqual(bg.header_key("source (repère)"), "repere")

    def test_status_normalisation(self):
        for raw, want in (("décidé", "decide"), ("à trancher", "ouvert"), ("Remplacée", "remplace"), ("périmé", "perime")):
            self.assertEqual(bg.norm_status(raw), want)


class Checks(unittest.TestCase):
    def base(self):
        return {"entites": [{"id": "E1", "statut": "actif"}, {"id": "E2", "statut": "actif"}], "liens": [], "decisions": [],
                "faits": [], "actions": [], "contradictions": []}

    def test_bitemporal_order(self):
        R = self.base()
        R["liens"] = [{"id": "L1", "source": "E1", "cible": "E2", "statut": "fait", "valid_at": "2026-05-02", "invalid_at": "2026-05-01",
                       "recorded_at": "2026-05-03", "expired_at": "2026-05-01"}]
        w = " ".join(bg.checks(R))
        self.assertIn("invalid_at antérieur à valid_at", w)
        self.assertIn("expired_at antérieur à recorded_at", w)

    def test_replaced_without_end(self):
        R = self.base()
        R["liens"] = [{"id": "L1", "source": "E1", "cible": "E2", "statut": "remplacé"}]
        self.assertTrue(any("remplacé sans invalid_at" in a for a in bg.checks(R)))

    def test_decided_needs_maker_and_proof(self):
        R = self.base()
        R["decisions"] = [{"id": "D1", "statut": "décidé", "entites": "E1"}]
        w = " ".join(bg.checks(R))
        self.assertIn("décidé sans décideur ou sans preuve", w)
        self.assertIn("décidé sans valid_at", w)

    def test_broken_link_and_bad_date(self):
        R = self.base()
        R["liens"] = [{"id": "L1", "source": "E1", "cible": "E9", "statut": "fait", "valid_at": "12/05/2026"}]
        w = " ".join(bg.checks(R))
        self.assertIn("cible E9 absente", w)
        self.assertIn("format AAAA-MM-JJ", w)


class Build(unittest.TestCase):
    def test_example_has_no_alert_and_a_diff(self):
        out, summary = run(EXAMPLE, "--precedent", PREVIOUS)
        self.assertEqual(summary["alertes"], [])
        data = json.load(open(os.path.join(out, "graphe.json"), encoding="utf-8"))
        ids = {i["id"] for i in data["diff"]["items"]}
        self.assertIn("D06", ids)
        self.assertTrue(os.path.getsize(os.path.join(out, "handover.md")) > 500)

    def test_page_is_self_contained(self):
        out, _ = run(EXAMPLE)
        page = open(os.path.join(out, "graphe.html"), encoding="utf-8").read()
        self.assertIn("default-src 'none'", page)
        self.assertNotRegex(page, r'<(script|link|img)[^>]+(src|href)="https?://')
        self.assertNotIn("__DATA__", page)
        self.assertNotIn("/*__D3__*/", page)
        self.assertIn("font/woff2;base64", page)

    def test_injection_is_escaped(self):
        reg = write({"Config": [["cle", "valeur"], ["projet", "<b>x</b>"], ["constat", "</script><script>alert(1)</script>"]],
                     "Entités": [["id", "libellé", "statut"], ["E1", "<img src=x onerror=alert(2)>", "actif"]]})
        out, _ = run(reg)
        page = open(os.path.join(out, "graphe.html"), encoding="utf-8").read()
        data_block = page.split('id="graphe-data" type="application/json">', 1)[1].split("</script>", 1)[0]
        self.assertNotIn("</script>", data_block)
        self.assertIn("<title>Graphe : &lt;b&gt;x&lt;/b&gt;</title>", page)

    def test_vendor_tampering_is_refused(self):
        tmp = tempfile.mkdtemp()
        subprocess.run(["cp", "-r", SCRIPTS, tmp], check=True)
        copy = os.path.join(tmp, "scripts")
        with open(os.path.join(copy, "vendor", "d3.min.js"), "a", encoding="utf-8") as f:
            f.write("\n// modifié")
        res = subprocess.run([sys.executable, "-I", os.path.join(copy, "build_graph.py"), EXAMPLE, tempfile.mkdtemp()], capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("empreinte", res.stderr)


if __name__ == "__main__":
    unittest.main()
