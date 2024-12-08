# app.py

from flask import Flask, request, Response, render_template
from flask_cors import CORS
import requests
from utils import get_rig_data, convert_rdf_to_jsonld, extract_suggestions

app = Flask(__name__)
CORS(app)
RDG_FILE = 'rdg_cache.xml'  # File to store the RDG


@app.route('/')
def home():
    return render_template('index.html') 


@app.route('/get_rdg', methods=['POST'])
def get_rdg():
    input_data = request.json
    remote_service_url = input_data.get('remote_service_url')

    if not remote_service_url:
        return Response("<error>remote_service_url is required</error>", status=400, mimetype='application/xml')

    try:
        rdg_response = requests.get(remote_service_url)
        rdg_response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return Response(f"<error>{str(e)}</error>", status=500, mimetype='application/xml')

    rdg_content = rdg_response.content.decode('utf-8')
    # print("RDG Response Content:", rdg_content)

    if not rdg_content.strip():
        return Response("<error>Received empty response from the remote service.</error>", status=500, mimetype='application/xml')

    with open(RDG_FILE, 'wb') as file:
        file.write(rdg_response.content)

    return Response(rdg_response.content, status=rdg_response.status_code, mimetype='application/xml')


@app.route('/book_cottage', methods=['POST'])
def book_cottage():
    # Step 1: Receive input data from the client
    input_data = request.json
    remote_service_url = "http://127.0.0.1:5001/cottages/search"

    # Validate input
    if not remote_service_url:
        return Response("<error>remote_service_url is required</error>", status=400, mimetype='application/xml')

    try:
        app.logger.info(f"----------input-data------------------")
        data = get_rig_data(input_data)
        app.logger.info(data)
        rig_response = requests.post(remote_service_url, json=data, headers={"Content-Type": "application/rdf+xml"})
        app.logger.info(f"---------------response------------------")
        # app.logger.info(f"{rig_response.content}")
        rrg_resp = convert_rdf_to_jsonld(rig_response.content)
        formated_response = extract_suggestions(rrg_resp)

        return {"response": formated_response, "status": "success"}
        rig_response.raise_for_status()  # Raise an error for bad responses
    except requests.exceptions.RequestException as e:
        return Response(f"<error>Failed to invoke remote service: {str(e)}</error>", status=500, mimetype='application/xml')


    # return Response(rig_response.content, status=rig_response.status_code, mimetype='application/xml')

if __name__ == '__main__':
    app.run(debug=True)
