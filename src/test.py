from SPARQLWrapper import SPARQLWrapper, JSON
import requests

# SPARQL Endpoint Configuration
sparql = SPARQLWrapper("http://publications.europa.eu/webapi/rdf/sparql")
sparql.setQuery("""
    PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
    SELECT ?celex WHERE {
        ?doc a cdm:legal_resource ;
             cdm:oj_series_type "L" ;
             cdm:resource_legal_date_document "2025-02-14"^^xsd:date ;
             owl:sameAs ?celex_uri .
        BIND(STRAFTER(STR(?celex_uri), "celex:") AS ?celex)
    }
""")
sparql.setReturnFormat(JSON)
results = sparql.query().convert()

# Fetch Full Metadata via REST API
for result in results["results"]["bindings"]:
    print(result)
    celex = result["celex"]["value"]
    api_url = f"https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:{celex}"
    response = requests.get(api_url)
    print(f"Document {celex}: {response.url}")