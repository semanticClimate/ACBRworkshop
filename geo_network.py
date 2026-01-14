# =========================
# PMC–Country–Continent Network (Dynamic, Single Cell)
# =========================

# Install required libraries (Colab-safe)
!pip -q install pycountry pycountry-convert

import pandas as pd
import re, json
import networkx as nx
from collections import defaultdict
from IPython.display import HTML, display
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

# -------- Wikipedia / Wikidata helpers --------
def wikipedia_url(title):
    title = title.replace(" ", "_")
    return f"https://en.wikipedia.org/wiki/{title}"

def wikidata_search_url(title):
    return f"https://www.wikidata.org/wiki/Special:Search?search={title.replace(' ', '%20')}"

# -------- Colors --------
color_map = {
    "PMC": "#0055ff",
    "COUNTRY": "#e377c2",
    "CONTINENT": "#2ca02c"
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

    # PMC node (PubMed Central)
    G.add_node(
        pmc,
        type="PMC",
        url=f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmc}/"
    )

    for country in countries:
        continent = country_to_continent(country)

        # Country node (Wikipedia)
        G.add_node(
            country,
            type="COUNTRY",
            url=wikipedia_url(country)
        )

        # Continent node (Wikipedia)
        G.add_node(
            continent,
            type="CONTINENT",
            url=wikipedia_url(continent)
        )

        # PMC → Country (row-level frequency)
        edge_weights[(pmc, country)] += 1
        G.add_edge(pmc, country)

        # Country → Continent (structural)
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

# -------- Render Cytoscape.js --------
display(HTML(f"""
<div id="cy" style="width:100%; height:750px; border:1px solid #ccc;"></div>

<script src="https://unpkg.com/cytoscape@3.21.2/dist/cytoscape.min.js"></script>

<script>
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
</script>
"""))
