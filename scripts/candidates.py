"""Normalise Coefficient Giving + EA Funds exports into one schema and
filter to AI-safety-candidate grants. Writes data/candidates.csv."""
import re, sys, hashlib
import pandas as pd

CG, EAF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

MONTHS = {m: i for i, m in enumerate(
    "January February March April May June July August September October November December".split(), 1)}

AI_RE = re.compile(
    r"\b(AI|A\.I\.|AGI|artificial intelligence|machine learning|\bML\b|alignment|interpretab|"
    r"deep learning|neural net|language model|LLM|frontier model|transformative|superintelligen|"
    r"MATS|SERI|AI safety|compute|evals?\b|evaluations|red.?team|jailbreak|mechanistic|"
    r"reward model|RLHF|agent foundations|corrigib|existential risk from|x-risk|catastrophic risk)",
    re.I)

BOILER = re.compile(r"(Grant Investigator:.*?\n|This page was reviewed.*?publication\.|"
                    r"Open Philanthropy recommended a grant of|Coefficient Giving recommended a grant of)",
                    re.I | re.S)


def clean(t):
    t = BOILER.sub(" ", str(t or ""))
    return re.sub(r"\s+", " ", t).strip()


def gid(*parts):
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:12]


rows = []

cg = pd.read_csv(CG)
for _, r in cg.iterrows():
    fa = str(r["Focus Area"])
    desc = clean(r["Details"])
    text = f'{r["Grant"]} {desc}'
    core = fa == "Navigating Transformative AI"
    maybe = fa in {"Global Catastrophic Risks", "Global Catastrophic Risks Capacity Building",
                   "Forecasting", "Effective Giving & Careers", "Other Areas"} and AI_RE.search(text)
    if not (core or maybe):
        continue
    m = str(r["Date"]).split()
    ym = f"{m[1]}-{MONTHS.get(m[0], 1):02d}" if len(m) == 2 else ""
    amt = float(re.sub(r"[^0-9.]", "", str(r["Amount"])) or 0)
    rows.append(dict(id="cg_" + gid(r["Grant"], r["Date"], amt), source="Coefficient Giving",
                     funder="Coefficient Giving", grantee=r["Organization Name"], title=r["Grant"],
                     amount=amt, date=ym, year=int(m[1]) if len(m) == 2 else None,
                     source_area=fa, scope="core" if core else "keyword", desc=desc[:700]))

ea = pd.read_csv(EAF)
for _, r in ea.iterrows():
    fund = str(r["fund"])
    if fund not in {"Long-Term Future Fund", "EA Infrastructure Fund", "Effective Altruism Infrastructure Fund"}:
        continue
    text = f'{r["grantee"]} {r["description"]}'
    hit = AI_RE.search(text)
    # LTFF is mostly AI safety but also funds biosecurity/other x-risk; keep all LTFF for review.
    if fund != "Long-Term Future Fund" and not hit:
        continue
    q = str(r["round"])
    qm = re.search(r"Q(\d)", q)
    ym = f'{int(r["year"])}-{(int(qm.group(1)) - 1) * 3 + 1:02d}' if qm else f'{int(r["year"])}-01'
    rows.append(dict(id="eaf_" + str(r["id"]), source="EA Funds", funder=fund.replace("Effective Altruism", "EA"),
                     grantee=r["grantee"], title=str(r["description"])[:140], amount=float(r["amount"] or 0),
                     date=ym, year=int(r["year"]), source_area=fund,
                     scope="keyword" if hit else "ltff_unmatched", desc=clean(r["description"])[:700]))

df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
print(df.groupby(["source", "scope"]).agg(n=("id", "size"), usd=("amount", "sum")))
