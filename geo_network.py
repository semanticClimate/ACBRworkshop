# =========================
# PMC–Country–Continent Network (Dynamic, Colab-ready)
# =========================

import pandas as pd
import re, json
import networkx as nx
from collections import defaultdict
import pycountry
import pycountry_convert as pc

# -------- INPUT CSV --------
csv_file = "/content/result_drug_data/fin_disData.csv"
df = pd.read_csv(csv_file)

# -------- Dynamic Country → Continent function --------
def country_to_continent(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        country_alpha2 = country.alpha_2
        continent_code = pc.country_alpha2_to_continent_code(country_alpha2)
        return pc.convert_continent_code_to_continent_name(continent_code)
    except Exception:
        return "Unknown"

# -------- Wikipedia helpers --------
def wikipedia_url(title):
    title = title.replace(" ", "_")
    return f"https://en.wikipedia.org/wiki/{title}"

# -------- Colors --------
color_map = {
    "PMC": "#3b71cd",
    "COUNTRY": "#e377c2",
    "CONTINENT": "#5A4E11"
}

# -------- Build graph --------
G = nx.Graph()
edge_weights = defaultdict(int)

for _, row in df.iterrows():
    file_path = str(row["file_path"])
    match = re.search(r"(PMC\d+)", file_path)
    if not match:
        continue

    pmc = match.group(1)

    countries = {
        c.strip() for c in str(row["0"]).split(",") if c.strip()
    }

    # PMC node
    G.add_node(
        pmc,
        type="PMC",
        url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"
    )

    for country in countries:
        continent = country_to_continent(country)

        G.add_node(
            country,
            type="COUNTRY",
            url=wikipedia_url(country)
        )

        G.add_node(
            continent,
            type="CONTINENT",
            url=wikipedia_url(continent)
        )

        edge_weights[(pmc, country)] += 1
        G.add_edge(pmc, country)
        G.add_edge(country, continent)

# -------- Assign edge weights --------
for (s, t), w in edge_weights.items():
    if G.has_edge(s, t):
        G[s][t]["weight"] = w

# -------- Export GraphML --------
graphml_path = "/content/pmc_country_continent.graphml"
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

# -------- Save HTML for Colab --------
html_path = "/content/pmc_country_continent.html"

with open(html_path, "w") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>PMC–Country–Continent Network</title>
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
