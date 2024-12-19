from flask import Flask, request, Response, render_template, jsonify
from flask_cors import CORS
import requests
from utils import get_rig_data, convert_rdf_to_jsonld, extract_suggestions
from ontology_alignment import OntologyAligner
import hashlib
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)
RDG_FILE = 'rdg_cache.xml'  # File to store the RDG
aligner = OntologyAligner()

def get_service_id(url):
    """Generate a unique ID for a service based on its URL"""
    return hashlib.md5(url.encode()).hexdigest()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/get_rdg', methods=['POST'])
def get_rdg():
    input_data = request.json
    remote_service_url = input_data.get('remote_service_url')
    alignment_method = input_data.get('alignment_method', 'custom')  # 'custom', 'api', or 'combined'

    if not remote_service_url:
        return Response("<e>remote_service_url is required<e>", status=400, mimetype='application/xml')

    try:
        logger.debug(f"Fetching RDG from: {remote_service_url}")
        rdg_response = requests.get(remote_service_url)
        rdg_response.raise_for_status()
        
        # Get service ID
        service_id = get_service_id(remote_service_url)
        logger.debug(f"Service ID: {service_id}")
        
        # Create new alignment using specified method
        alignment = aligner.align_ontologies(
            rdg_response.content,
            open('reference_ontology.rdf', 'rb').read(),
            method=alignment_method
        )
        logger.debug(f"New alignment created with {len(alignment) if alignment else 0} mappings")
        
        # Return all alignments with their confidence scores
        return jsonify({
            'status': 'success',
            'alignments': alignment
        })
        
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching RDG: {str(e)}"
        logger.error(error_msg)
        return Response(f"<e>{error_msg}</e>", status=500, mimetype='application/xml')

@app.route('/confirm_alignment', methods=['POST'])
def confirm_alignment():
    data = request.json
    service_id = data.get('service_id')
    confirmed_alignments = data.get('alignments')
    
    if not service_id or not confirmed_alignments:
        return jsonify({'error': 'Missing service_id or alignments'}), 400
        
    # Load existing alignment
    alignment = aligner.load_alignment(service_id)
    if not alignment:
        return jsonify({'error': 'No alignment found for this service'}), 404
        
    # Update alignment with confirmed mappings
    for confirmed in confirmed_alignments:
        for a in alignment:
            if a['source_uri'] == confirmed['source_uri']:
                a.update(confirmed)
                a['needs_confirmation'] = False
                
    # Save updated alignment
    aligner.save_alignment(service_id, alignment)
    return jsonify({'status': 'success'})

@app.route('/book_cottage', methods=['POST'])
def book_cottage():
    input_data = request.json
    remote_service_url = input_data.get('remote_service_url', "http://127.0.0.1:5001/cottages/search")
    service_id = get_service_id(remote_service_url)

    if not remote_service_url:
        return Response("<e>remote_service_url is required<e>", status=400, mimetype='application/xml')

    try:
        # Load alignment for this service
        alignment = aligner.load_alignment(service_id)
        if not alignment:
            return jsonify({'error': 'No alignment found for this service'}), 400
            
        # Transform input data using alignment
        transformed_data = transform_data_using_alignment(input_data, alignment)
        
        # Send transformed data to remote service
        response = requests.post(
            f"{remote_service_url}/book",
            json=transformed_data,
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        
        # Transform response back using reverse alignment
        transformed_response = transform_response_using_alignment(response.json(), alignment)
        
        return jsonify(transformed_response)
        
    except requests.exceptions.RequestException as e:
        return Response(f"<e>{str(e)}<e>", status=500, mimetype='application/xml')

def transform_data_using_alignment(data, alignment):
    """Transform input data using ontology alignment"""
    transformed = {}
    alignment_map = {a['source_uri']: a['target_uri'] for a in alignment}
    
    for key, value in data.items():
        if key in alignment_map:
            transformed[alignment_map[key]] = value
        else:
            transformed[key] = value
            
    return transformed

def transform_response_using_alignment(data, alignment):
    """Transform response data using reverse ontology alignment"""
    transformed = {}
    alignment_map = {a['target_uri']: a['source_uri'] for a in alignment}
    
    for key, value in data.items():
        if key in alignment_map:
            transformed[alignment_map[key]] = value
        else:
            transformed[key] = value
            
    return transformed

if __name__ == '__main__':
    app.run(debug=True)
