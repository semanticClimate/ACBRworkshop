# =========================
# PMC–Disease Network (Dynamic, Colab-ready)
# =========================

import pandas as pd
import re, json
import networkx as nx
from collections import defaultdict
import argparse

# -------- Command-line arguments --------
parser = argparse.ArgumentParser(description="PMC–Disease Network")
parser.add_argument("--input", type=str, required=True, help="Path to input CSV file")
parser.add_argument("--graphml", type=str, required=True, help="Path to save GraphML file")
parser.add_argument("--html", type=str, required=True, help="Path to save HTML file")
args = parser.parse_args()

csv_file = args.input
graphml_path = args.graphml
html_path = args.html

# -------- Load CSV --------
df = pd.read_csv(csv_file)

# -------- Wikipedia helper --------
def wikipedia_url(title):
    title = title.replace(" ", "_")
    return f"https://en.wikipedia.org/wiki/{title}"

# -------- Colors --------
color_map = {
    "PMC": "#3b71cd",
    "DISEASE": "#d62728"
}

# -------- Build graph --------
G = nx.Graph()
edge_weights = defaultdict(int)

for _, row in df.iterrows():

    # ---- Extract PMC ID ----
    file_path = str(row["file_path"])
    match = re.search(r"(PMC\d+)", file_path)
    if not match:
        continue
    pmc = match.group(1)

    # ---- Diseases (unique per row, no inflation) ----
    diseases = {
        d.strip()
        for d in str(row["0"]).split(",")
        if d.strip()
    }

    # ---- PMC node ----
    G.add_node(
        pmc,
        type="PMC",
        url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"
    )

    for disease in diseases:

        # ---- Disease node ----
        G.add_node(
            disease,
            type="DISEASE",
            url=wikipedia_url(disease)
        )

        # ---- PMC → Disease edge (row-level count) ----
        edge_weights[(pmc, disease)] += 1
        G.add_edge(pmc, disease)

# -------- Assign edge weights --------
for (s, t), w in edge_weights.items():
    if G.has_edge(s, t):
        G[s][t]["weight"] = w

# -------- Export GraphML --------
nx.write_graphml(G, graphml_path)
print(f"✔ GraphML exported for Cytoscape Desktop: {graphml_path}")

# -------- Convert to Cytoscape elements --------
elements = []

for n, d in G.nodes(data=True):
    elements.append({
        "data": {
            "id": n,
            "label": n,
            "type": d["type"],
            "color": color_map.get(d["type"], "#cccccc"),
            "url": d.get("url")
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

# -------- Save HTML --------
with open(html_path, "w") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PMC–Disease Network</title>
<script src="https://unpkg.com/cytoscape@3.21.2/dist/cytoscape.min.js"></script>
</head>
<body>

<div id="cy" style="width:100%; height:750px; border:1px solid #ccc;"></div>

<script>
document.addEventListener("DOMContentLoaded", function() {{
  var cy = cytoscape({{
    container: document.getElementById('cy'),
    elements: {json.dumps(elements)},
    style: [
      {{
        selector: 'node',
        style: {{
          'label': 'data(label)',
          'background-color': 'data(color)',
          'font-size': '10px',
          'text-valign': 'center',
          'text-halign': 'center'
        }}
      }},
      {{
        selector: 'edge',
        style: {{
          'width': 'mapData(weight, 1, 10, 1, 6)',
          'line-color': '#999'
        }}
      }}
    ],
    layout: {{ name: 'cose' }}
  }});

  cy.on('tap', 'node', function(evt) {{
    const url = evt.target.data('url');
    if (url) {{
      window.open(url, '_blank');
    }}
  }});
}});
</script>

</body>
</html>
""")

print(f"✔ Interactive HTML saved: {html_path}")
