# =========================
# Country–Disease–Drug–PMC Network
# =========================

import pandas as pd
import re, json
import networkx as nx
from collections import defaultdict
import argparse

# -------- CLI arguments --------
parser = argparse.ArgumentParser()
parser.add_argument("--country", required=True, help="Country CSV")
parser.add_argument("--disease", required=True, help="Disease CSV")
parser.add_argument("--drug", required=True, help="Drug CSV")
parser.add_argument("--graphml", required=True)
parser.add_argument("--html", required=True)
args = parser.parse_args()

# -------- Load CSVs --------
df_country = pd.read_csv(args.country)
df_disease = pd.read_csv(args.disease)
df_drug = pd.read_csv(args.drug)

# -------- Helpers --------
def wiki(title):
    return f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}"

def pmc_url(pmc):
    return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"

def extract_pmc(path):
    m = re.search(r"(PMC\d+)", str(path))
    return m.group(1) if m else None

# -------- Graph --------
G = nx.Graph()
edge_w = defaultdict(int)

# -------- COLORS --------
COLORS = {
    "PMC": "#3b71cd",
    "COUNTRY": "#2ca02c",
    "DISEASE": "#9467bd",
    "DRUG": "#d62728"
}

# ========================
# COUNTRY → PMC
# ========================
for _, r in df_country.iterrows():
    pmc = extract_pmc(r["file_path"])
    if not pmc: continue

    countries = {c.strip() for c in str(r["0"]).split(",") if c.strip()}

    G.add_node(pmc, type="PMC", url=pmc_url(pmc))

    for c in countries:
        G.add_node(c, type="COUNTRY", url=wiki(c))
        edge_w[(pmc, c)] += 1
        G.add_edge(pmc, c)

# ========================
# DISEASE → PMC
# ========================
for _, r in df_disease.iterrows():
    pmc = extract_pmc(r["file_path"])
    if not pmc: continue

    diseases = {d.strip().lower() for d in str(r["0"]).split(",") if d.strip()}

    for d in diseases:
        d = d.capitalize()
        G.add_node(d, type="DISEASE", url=wiki(d))
        edge_w[(pmc, d)] += 1
        G.add_edge(pmc, d)

# ========================
# DRUG → PMC + DISEASE
# ========================
for _, r in df_drug.iterrows():
    pmc = extract_pmc(r["file_path"])
    if not pmc: continue

    drugs = {d.strip().lower() for d in str(r["0"]).split(",") if d.strip()}

    for drug in drugs:
        drug = drug.capitalize()
        G.add_node(drug, type="DRUG", url=wiki(drug))
        edge_w[(pmc, drug)] += 1
        G.add_edge(pmc, drug)

        # disease–drug association (if disease column exists)
        if "disease" in r:
            disease = r["disease"].capitalize()
            G.add_node(disease, type="DISEASE", url=wiki(disease))
            edge_w[(disease, drug)] += 1
            G.add_edge(disease, drug)

# -------- Assign weights --------
for (s, t), w in edge_w.items():
    if G.has_edge(s, t):
        G[s][t]["weight"] = w

# -------- Export GraphML --------
nx.write_graphml(G, args.graphml)
print("✔ GraphML exported")

# -------- Cytoscape HTML --------
elements = []

for n, d in G.nodes(data=True):
    elements.append({
        "data": {
            "id": n,
            "label": n,
            "type": d["type"],
            "color": COLORS[d["type"]],
            "url": d["url"]
        }
    })

for s, t, d in G.edges(data=True):
    elements.append({
        "data": {
            "source": s,
            "target": t,
            "weight": d.get("weight", 1)
        }
    })

with open(args.html, "w") as f:
    f.write(f"""
<html>
<head>
<script src="https://unpkg.com/cytoscape@3.21.2/dist/cytoscape.min.js"></script>
</head>
<body>
<div id="cy" style="width:100%;height:800px;"></div>
<script>
cytoscape({{
 container: document.getElementById('cy'),
 elements: {json.dumps(elements)},
 style: [
  {{ selector: 'node', style: {{
    'label':'data(label)',
    'background-color':'data(color)',
    'font-size':'10px'
  }} }},
  {{ selector:'edge', style:{{
    'width':'mapData(weight,1,10,1,6)'
  }} }}
 ],
 layout: {{ name:'cose' }}
}})
.on('tap','node',e=>window.open(e.target.data('url'),'_blank'));
</script>
</body>
</html>
""")

print("✔ Interactive HTML saved")
