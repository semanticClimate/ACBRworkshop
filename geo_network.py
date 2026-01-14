def build_pmc_country_continent_network(
    input_csv,
    output_graphml,
    render_html=True
):
    import pandas as pd
    import re, json, urllib.parse
    import networkx as nx
    from collections import defaultdict
    from IPython.display import HTML, display
    import pycountry
    import pycountry_convert as pc

    # -------------------------------
    # Helper: Country → Continent
    # -------------------------------
    def country_to_continent(country_name):
        try:
            country = pycountry.countries.lookup(country_name)
            continent_code = pc.country_alpha2_to_continent_code(country.alpha_2)
            return pc.convert_continent_code_to_continent_name(continent_code)
        except Exception:
            return "Unknown"

    # -------------------------------
    # Helper: Node → External URL
    # -------------------------------
    def node_to_url(node, node_type):
        if node_type == "PMC":
            return f"https://www.ncbi.nlm.nih.gov/pmc/articles/{node}/"

        if node_type in {"COUNTRY", "CONTINENT"}:
            title = urllib.parse.quote(node.replace(" ", "_"))
            return f"https://en.wikipedia.org/wiki/{title}"

        # Generic Wikidata fallback
        query = urllib.parse.quote(node)
        return f"https://www.wikidata.org/wiki/Special:Search?search={query}"

    # -------------------------------
    # Colors
    # -------------------------------
    color_map = {
        "PMC": "#0055ff",
        "COUNTRY": "#e377c2",
        "CONTINENT": "#2ca02c"
    }

    df = pd.read_csv(input_csv)

    G = nx.Graph()
    edge_weights = defaultdict(int)

    # -------------------------------
    # Build graph
    # -------------------------------
    for _, row in df.iterrows():
        match = re.search(r"(PMC\d+)", str(row["file_path"]))
        if not match:
            continue

        pmc = match.group(1)
        countries = {c.strip() for c in str(row["0"]).split(",") if c.strip()}

        G.add_node(
            pmc,
            type="PMC",
            url=node_to_url(pmc, "PMC")
        )

        for country in countries:
            continent = country_to_continent(country)

            G.add_node(
                country,
                type="COUNTRY",
                url=node_to_url(country, "COUNTRY")
            )

            G.add_node(
                continent,
                type="CONTINENT",
                url=node_to_url(continent, "CONTINENT")
            )

            edge_weights[(pmc, country)] += 1
            G.add_edge(pmc, country)
            G.add_edge(country, continent)

    for (s, t), w in edge_weights.items():
        if G.has_edge(s, t):
            G[s][t]["weight"] = w

    # -------------------------------
    # Export GraphML (links preserved)
    # -------------------------------
    nx.write_graphml(G, output_graphml)

    # -------------------------------
    # Render Cytoscape.js
    # -------------------------------
    if render_html:
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

        display(HTML(f"""
        <div id="cy" style="width:100%; height:750px;"></div>
        <script src="https://unpkg.com/cytoscape@3.21.2/dist/cytoscape.min.js"></script>
        <script>
        var cy = cytoscape({{
          container: document.getElementById('cy'),
          elements: {json.dumps(elements)},
          layout: {{ name: 'cose' }},
          style: [
            {{
              selector: 'node',
              style: {{
                'label': 'data(label)',
                'background-color': 'data(color)',
                'font-size': '10px'
              }}
            }},
            {{
              selector: 'edge',
              style: {{
                'width': 'mapData(weight,1,10,1,6)'
              }}
            }}
          ]
        }});

        cy.on('tap', 'node', function(evt) {{
          const url = evt.target.data('url');
          if (url) {{
            window.open(url, '_blank');
          }}
        }});
        </script>
        """))