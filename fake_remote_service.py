from flask import Flask, request, Response
from rdflib import Graph
import os

app = Flask(__name__)

def convert_ttl_to_rdf_xml(ttl_content):
    """Convert Turtle format to RDF/XML"""
    g = Graph()
    try:
        # Parse the content as Turtle
        g.parse(data=ttl_content, format='turtle')
        # Serialize to RDF/XML
        return g.serialize(format='xml')
    except Exception as e:
        print(f"Error converting TTL to RDF/XML: {str(e)}")
        return None

@app.route('/CottageBookingService')
def rdg():
    """Return RDG.ttl content as RDF/XML"""
    try:
        rdg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               'Ontologies of other teams', 'Team01', 'RDG.ttl')
        with open(rdg_path, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
        
        rdf_content = convert_ttl_to_rdf_xml(ttl_content)
        if rdf_content:
            return Response(rdf_content, mimetype='application/rdf+xml')
        else:
            return Response("Error converting TTL to RDF/XML", status=500)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=500)

@app.route('/')
def home():
    return "Fake Remote Service"

@app.route('/book', methods=['POST'])
def book_cottage():
    """Return RRG.ttl content as RDF/XML after receiving booking request"""
    try:
        rrg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                               'Ontologies of other teams', 'Team01', 'RRG.ttl')
        with open(rrg_path, 'r', encoding='utf-8') as f:
            ttl_content = f.read()
            
        rdf_content = convert_ttl_to_rdf_xml(ttl_content)
        if rdf_content:
            return Response(rdf_content, mimetype='application/rdf+xml')
        else:
            return Response("Error converting TTL to RDF/XML", status=500)
    except Exception as e:
        return Response(f"Error: {str(e)}", status=404)

if __name__ == '__main__':
    app.run(port=5002)
