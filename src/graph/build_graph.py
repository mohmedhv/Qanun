"""Week 3 - build the legal knowledge graph (NetworkX) and write it as CSV files.

Run:  python -m src.graph.build_graph
Reads : data/db/qanun.db  (tables texts, articles, relations, versions, amendment_verification)
        data/interim/evolution_blocks.json  ("Textes d'application" lines -> `applies` edges)
Writes: data/graph/nodes.csv, data/graph/edges.csv   (same input -> same files, byte for byte)

Nodes  : Text, Article, Version
Edges  : belongs_to (Article->Text, Version->Article)
         modifies / repeals / adds   (Text->Article, from `relations`; plus the Text->Text summary links)
         applies                     (decree -> article, from the portal's "Textes d'application" lists)
         cites                       (Article->Article, regex on the article content)
"""
import argparse
import csv
import json
import re
import sqlite3
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[2]
DB_PATH = ROOT / "data/db/qanun.db"
EVOLUTION_PATH = ROOT / "data/interim/evolution_blocks.json"
OUT_DIR = ROOT / "data/graph"
LAW = "loi-90-11"

MONTHS = "janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre"
MONTH_NUM = {m: i for i, m in enumerate(MONTHS.split("|"), 1)}
STATUS_ORDER = ["a_verifier", "verifie_copie_publiee", "verifie_jo_officiel"]   # worst first


# ---------------------------------------------------------------- applies (decrees)
ENTRY = re.compile(
    r"(?P<type>Décret (?:exécutif|présidentiel|législatif)|Décret|Arrêté(?: interministériel| ministériel)?)\s+"
    r"n°\s*(?P<num>\d+-\d+)\s+du\s+(?P<head>.{0,400}?)\(page\s*\d+\)[^()]{0,80}?"
    r"\(Publié\s+dans\s+JO\s+n°\s*(?P<jo>\d+)\s+du\s+(?P<jodate>\d{2}/\d{2}/\d{4})\)",
    re.S,
)
GREG_DATE = re.compile(rf"(\d{{1,2}}|1er)\s+({MONTHS})\s+(\d{{4}})")


def slug(kind: str, number: str) -> str:
    return re.sub(r"[^a-z]+", "-", kind.lower().replace("é", "e").replace("è", "e")).strip("-") + "-" + number


def parse_applications(blocks: list[dict]) -> list[dict]:
    """One dict per (decree, article) listed under "Textes d'application" in the annotated copy.
    Only decrees/arrêtés are kept: laws and ordinances in those lists are amending or related texts."""
    found = {}
    for block in blocks:
        text = block["text"]
        if "Textes d’application" not in text:
            continue
        text = text.split("\nMouture de", 1)[0]        # after this line the portal copies ANOTHER text's page
        for m in ENTRY.finditer(text):
            head = " ".join(m.group("head").split())
            dates = GREG_DATE.findall(head)
            day, month, year = dates[0] if dates else (None, None, None)
            date_signed = None
            if day:
                date_signed = f"{int(year):04d}-{MONTH_NUM[month]:02d}-{1 if day == '1er' else int(day):02d}"
            d, mth, y = m.group("jodate").split("/")
            title = re.split(r"\d{4}\s+", head, maxsplit=1)[-1] if dates else head
            kind = m.group("type")
            key = (slug(kind, m.group("num")), block["article"])
            found[key] = {
                "text_id": key[0], "type": slug(kind, "").strip("-"), "number": m.group("num"),
                "date_signed": date_signed, "jo_number": f"JO n°{int(m.group('jo'))}",
                "jo_date": f"{y}-{mth}-{d}", "title": title.strip(" ,.;"),
                "article": block["article"],
                "source_url": f"https://www.joradp.dz/FTP/jo-francais/{y}/F{y}{int(m.group('jo')):03d}.pdf",
            }
    return [found[k] for k in sorted(found, key=lambda k: (int(k[1]), k[0]))]


# ---------------------------------------------------------------- cites (regex)
ART_REF = re.compile(
    r"\barticles?\s+(?P<first>\d+(?:-\d+)?(?:\s+(?:bis|ter|quater)(?:\s+\d+)?)?)"
    r"(?P<more>(?:\s*(?:,|et|à)\s*\d+(?:-\d+)?(?:\s+(?:bis|ter|quater)(?:\s+\d+)?)?)*)", re.I)
EXTERNAL = re.compile(r"^\W{0,3}(?:de|du|des)\s+(?:la\s+loi|l[’']ordonnance|l[’']ordonnance|code|décret|constitution)\b"
                      r"(?!\s+présente)", re.I)


def article_id(number: str) -> str:
    return f"{LAW}-art-{'-'.join(number.split())}"


def extract_cites(articles: list[dict]):
    """Returns (cites, rejected). cites = list of dicts; rejected = matches that probably point elsewhere."""
    known = {a["number"] for a in articles}
    cites, rejected = [], []
    for a in articles:
        content = a["content"]
        for m in ART_REF.finditer(content):
            tail = content[m.end():m.end() + 45]
            context = " ".join(content[max(0, m.start() - 30):m.end() + 45].split())
            numbers = [m.group("first")] + re.findall(r"\d+(?:-\d+)?(?:\s+(?:bis|ter|quater)(?:\s+\d+)?)?", m.group("more"))
            numbers = [" ".join(n.split()) for n in numbers]
            if EXTERNAL.search(tail):
                rejected.append((a["number"], numbers, "points to another text", context))
                continue
            for n in numbers:
                if n == a["number"]:
                    rejected.append((a["number"], [n], "self reference", context)); continue
                if n not in known:
                    rejected.append((a["number"], [n], "target article does not exist", context)); continue
                cites.append({"source": a["number"], "target": n, "context": context})
    return cites, rejected


# ---------------------------------------------------------------- the graph
def build_graph(db_path=DB_PATH, evolution_path=EVOLUTION_PATH, report=None) -> nx.MultiDiGraph:
    g = nx.MultiDiGraph()
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    texts = con.execute("SELECT * FROM texts ORDER BY text_id").fetchall()
    articles = [dict(r) for r in con.execute("SELECT * FROM articles ORDER BY sort_key, number")]
    relations = con.execute("SELECT * FROM relations ORDER BY relation_id").fetchall()
    versions = con.execute("SELECT * FROM versions ORDER BY version_id").fetchall()
    verif = con.execute("SELECT * FROM amendment_verification ORDER BY csv_row").fetchall()
    text_ids = {t["text_id"] for t in texts}
    article_ids = {a["article_id"] for a in articles}
    number_of = {a["article_id"]: a["number"] for a in articles}

    # Text nodes (the P3 loader already created them; we only read)
    for t in texts:
        g.add_node(f"text:{t['text_id']}", entity="Text", label=f"{t['type']} {t['number']}", type=t["type"],
                   number=t["number"], date_signed=t["date_signed"], jo_number=t["jo_number"],
                   jo_date=t["jo_date"], source_url=t["source_url"], origin="db")
    # Article nodes + belongs_to
    for a in articles:
        g.add_node(f"article:{a['article_id']}", entity="Article", label=f"art. {a['number']}", type="article",
                   number=a["number"], status=a["status"], source_url=a["source_url"], origin="db")
        g.add_edge(f"article:{a['article_id']}", f"text:{a['text_id']}", relation="belongs_to",
                   source_url=a["source_url"], status="structural", origin="db")
    # Version nodes + belongs_to (version -> its article)
    for v in versions:
        node = f"version:{v['version_id']}"
        g.add_node(node, entity="Version", label=f"art. {v['article_number']} v{v['version_number']}", type="version",
                   number=v["version_number"], status=v["status"], date_signed=v["valid_from"],
                   source_url=v["source_url"], origin="db")
        if v["article_id"] in article_ids:
            g.add_edge(node, f"article:{v['article_id']}", relation="belongs_to",
                       source_url=v["source_url"], status=v["verification_status"] or "structural", origin="db")

    # modifies / repeals / adds, read from `relations`; source + status come from amendment_verification
    by_pair = {}
    for r in verif:
        by_pair.setdefault((r["modifying_text_id"], r["target_article"]), []).append(r)
    for r in relations:
        src, dst = r["source_id"], r["target_id"]
        if src not in text_ids:
            continue
        if dst in article_ids or dst.startswith(f"{LAW}-art-"):
            suffix = dst[len(f"{LAW}-art-"):]
            number = number_of.get(dst) or re.sub(r"-(?=[a-z])|(?<=[a-z])-", " ", suffix)   # 56-bis-1 -> "56 bis 1", 73-1 stays
            if dst not in article_ids:                     # article created by an amendment (87 bis, 56 bis ...)
                g.add_node(f"article:{dst}", entity="Article", label=f"art. {number}", type="article", number=number,
                           status="created_by_amendment", source_url=None, origin="relations (not in the 158-article base)")
            rows = by_pair.get((src, number), [])
            status = min((x["verification_status"] for x in rows), key=STATUS_ORDER.index) if rows else "no_verification_row"
            source = rows[0]["source_url"] if rows else None
            g.add_edge(f"text:{src}", f"article:{dst}", relation=r["type"], source_url=source, status=status,
                       provision=" + ".join(x["provision"] for x in rows), origin="relations")
        elif dst in text_ids:                              # Text -> Text summary link, kept as it is
            g.add_edge(f"text:{src}", f"text:{dst}", relation=r["type"],
                       source_url=g.nodes[f"text:{src}"]["source_url"], status="summary_link", origin="relations")

    # applies: decrees listed under "Textes d'application" (not in `texts`, so they become new Text nodes)
    if Path(evolution_path).exists():
        blocks = json.loads(Path(evolution_path).read_text(encoding="utf-8"))
        for app in parse_applications(blocks):
            node = f"text:{app['text_id']}"
            if node not in g:
                g.add_node(node, entity="Text", label=f"{app['type']} {app['number']}", type=app["type"],
                           number=app["number"], date_signed=app["date_signed"], jo_number=app["jo_number"],
                           jo_date=app["jo_date"], source_url=app["source_url"], origin="evolution_blocks.json")
            target = article_id(app["article"])
            if target in article_ids:
                g.add_edge(node, f"article:{target}", relation="applies", source_url=app["source_url"],
                           status="portal_listed_unverified", origin="evolution_blocks.json")

    # cites
    cites, rejected = extract_cites(articles)
    for c in cites:
        g.add_edge(f"article:{article_id(c['source'])}", f"article:{article_id(c['target'])}", relation="cites",
                   source_url=g.nodes[f"article:{article_id(c['source'])}"]["source_url"],
                   status="regex_to_check", origin="article content")
    if report is not None:
        report.update(cites=cites, rejected=rejected)
    con.close()
    return g


# ---------------------------------------------------------------- integrity + output
def check(g: nx.MultiDiGraph) -> list[str]:
    problems = []
    for u, v, k, d in g.edges(keys=True, data=True):
        if u not in g or v not in g:
            problems.append(f"edge points to a missing node: {u} -> {v}")
        if d["relation"] in ("modifies", "repeals", "adds"):
            if not d.get("source_url"):
                problems.append(f"{d['relation']} edge without source: {u} -> {v}")
            if not d.get("status"):
                problems.append(f"{d['relation']} edge without status: {u} -> {v}")
            if d.get("status") == "no_verification_row":
                problems.append(f"{d['relation']} edge without verification row: {u} -> {v}")
    for n, d in g.nodes(data=True):
        if "entity" not in d:
            problems.append(f"node without entity (created by an edge): {n}")
    return problems


NODE_COLS = ["node_id", "entity", "label", "type", "number", "status", "date_signed", "jo_number", "jo_date", "source_url", "origin"]
EDGE_COLS = ["source", "target", "relation", "status", "source_url", "provision", "origin"]


def write_csv(g: nx.MultiDiGraph, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "nodes.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, NODE_COLS, lineterminator="\n"); w.writeheader()
        for n in sorted(g.nodes):
            w.writerow({"node_id": n, **{c: g.nodes[n].get(c, "") or "" for c in NODE_COLS[1:]}})
    edges = sorted(((u, v, d["relation"], d) for u, v, d in g.edges(data=True)), key=lambda e: e[:3] + (e[3].get("provision", ""),))
    with (out_dir / "edges.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, EDGE_COLS, lineterminator="\n"); w.writeheader()
        for u, v, rel, d in edges:
            w.writerow({"source": u, "target": v, "relation": rel, **{c: d.get(c, "") or "" for c in EDGE_COLS[3:]}})


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB_PATH))
    ap.add_argument("--out", default=str(OUT_DIR))
    ap.add_argument("--show-cites", action="store_true", help="print every `cites` match and every rejected match")
    a = ap.parse_args()
    report = {}
    g = build_graph(a.db, report=report)
    if a.show_cites:
        print("== cites kept (to check by hand)")
        for c in report["cites"]:
            print(f"  art. {c['source']:>6} -> art. {c['target']:<8} | {c['context']}")
        print("== matches rejected")
        for src, nums, why, ctx in report["rejected"]:
            print(f"  art. {src:>6} {nums} | {why} | {ctx}")
    write_csv(g, Path(a.out))
    nodes, edges = {}, {}
    for _, d in g.nodes(data=True):
        nodes[d.get("entity", "?")] = nodes.get(d.get("entity", "?"), 0) + 1
    for _, _, d in g.edges(data=True):
        edges[d["relation"]] = edges.get(d["relation"], 0) + 1
    print("nodes by type:", dict(sorted(nodes.items())), "| total", g.number_of_nodes())
    print("edges by type:", dict(sorted(edges.items())), "| total", g.number_of_edges())
    problems = check(g)
    print("INTEGRITY:", "OK, no problem" if not problems else f"{len(problems)} problem(s)")
    for p in problems:
        print("  PROBLEM", p)
    print(f"written: {Path(a.out) / 'nodes.csv'} and edges.csv")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
