from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, XSD
import requests, json
import xml.etree.ElementTree as ET
import io
from datetime import datetime


# Namespaces
COTTAGE = Namespace("http://localhost:8080/CottageBookingService/ontology#")
SSWAP = Namespace("http://sswapmeet.sswap.info/sswap/")
XSD = Namespace("http://www.w3.org/2001/XMLSchema#")

# Path to the RDF Turtle description file
rdg_file = "rdg_cache.xml"  # Update with the actual file path


import xml.etree.ElementTree as ET
import io

def get_rig_data(user_input):
    # Namespaces
    ns0 = "http://sswapmeet.sswap.info/sswap/"
    ns1 = "http://localhost:8080/CottageBookingService/ontology#"
    rdf_ns = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"

    # Register namespaces with meaningful prefixes
    ET.register_namespace("sswap", ns0)
    ET.register_namespace("cbs", ns1)
    ET.register_namespace("rdf", rdf_ns)

    # Parse the base RDG XML file
    tree = ET.parse(rdg_file)
    root = tree.getroot()

    # Locate the `<rdf:Description>` node where we'll add user input
    for description in root.findall("rdf:Description", {"rdf": rdf_ns}):
        if description.get(f"{{{rdf_ns}}}about") == "http://localhost:8080/CottageBookingService/CottageBookingService":
            # Add the new Graph structure
            operates_on = ET.SubElement(description, f"{{{ns0}}}operatesOn")
            graph = ET.SubElement(operates_on, f"{{{ns0}}}Graph")
            has_mapping = ET.SubElement(graph, f"{{{ns0}}}hasMapping")
            subject = ET.SubElement(has_mapping, f"{{{ns0}}}Subject")
            ET.SubElement(subject, "rdf:type", {f"{{{rdf_ns}}}resource": f"{ns1}Booking"})

            # Map user input to XML structure
            for key, value in user_input.items():
                if key == "nearestCity":  # If the field is a resource (e.g., nearestCity)
                    ET.SubElement(subject, f"{{{ns1}}}{key}", {
                        f"{{{rdf_ns}}}resource": f"{ns1}City_{value}"
                    })
                else:
                    datatype = "http://www.w3.org/2001/XMLSchema#string" if isinstance(value, str) else "http://www.w3.org/2001/XMLSchema#integer"
                    ET.SubElement(subject, f"{{{ns1}}}{key}", {f"{{{rdf_ns}}}datatype": datatype}).text = str(value)

            # Add mapsTo -> Object structure
            maps_to = ET.SubElement(subject, f"{{{ns0}}}mapsTo")
            obj = ET.SubElement(maps_to, f"{{{ns0}}}Object")
            ET.SubElement(obj, "rdf:type", {f"{{{rdf_ns}}}resource": f"{ns1}CottageSuggestion"})

            break

    # Serialize the updated XML tree to a string
    output = io.StringIO()
    tree.write(output, encoding="unicode", xml_declaration=True)
    rig_data = output.getvalue()
    output.close()

    return rig_data


# ... existing code ...
# def get_rig_data(client_input):
#     # Step 1: Load RDF Description from File
#     g_description = Graph()
#     g_description.parse(turtle_file_path, format="xml")

#     # Extract necessary attributes from RDF description (for validation or construction)
#     required_properties = [
#         COTTAGE.bookerName,
#         COTTAGE.maxDistanceToCity,
#         COTTAGE.maxDistanceToLake,
#         COTTAGE.maxShiftDays,
#         COTTAGE.nearestCity,
#         COTTAGE.requiredBedrooms,
#         COTTAGE.requiredDays,
#         COTTAGE.requiredPlaces,
#         COTTAGE.startDate
#     ]

#     # Step 2: Create Service Request (RIG)
#     g_request = Graph()
#     rig_subject = URIRef("http://example.org/request")
#     g_request.add((rig_subject, URIRef("http://www.w3.org/1999/02/22-rdf-syntax-ns#type"), COTTAGE.Booking))

#     # Add client input as RDF triples
#     for prop, value in client_input.items():
#         rdf_property = COTTAGE[prop]
#         literal_type = XSD.string
#         if isinstance(value, int):
#             literal_type = XSD.integer
#         elif "date" in prop.lower():
#             literal_type = XSD.date
#         g_request.add((rig_subject, rdf_property, Literal(value, datatype=literal_type)))

#     # Step 3: Serialize and POST the RIG
#     service_url = "http://remote-service-endpoint.example.org"  # Replace with actual endpoint
#     headers = {"Content-Type": "application/rdf+xml"}

#     rig_data = g_request.serialize(format="xml")
#     print(rig_data)
#     return rig_data


def convert_rdf_to_jsonld(rdf_data):
    # Initialize the RDF graph
    graph = Graph()
    print("parse data")
    # Parse the RDF/XML data
    graph.parse(data=rdf_data, format="xml")
    
    # Serialize the graph to JSON-LD format
    jsonld_data = graph.serialize(format="json-ld", indent=4)
    print(jsonld_data)
    
    return jsonld_data



def extract_suggestions(response):
    """
    This function takes a JSON response containing cottage suggestions and returns
    a formatted JSON list with key details extracted from the response.

    Args:
    - response (str): A JSON string containing the cottage suggestions.

    Returns:
    - str: A formatted JSON string containing a list of suggestions with key details.
    """
    # Parse the JSON response
    
    data = json.loads(response)
    print('-------------------------------------------')
    print(data)
    
    print("---------------parsing data -----------------------------")

    # Prepare a list to store formatted suggestions
    formatted_suggestions = []

    for item in data:
        type = item.get("@type", [])
        print(type)

        if type and type[-1].endswith("Booking"):
            bookerName = item.get("http://localhost:8080/CottageBookingService/ontology#bookerName", [{}])[0].get("@value")
        if type and type[0].endswith("CottageSuggestion"):
            cottage_data = {
                "bookingNumber": item.get("http://localhost:8080/CottageBookingService/ontology#bookingNumber", [{}])[0].get("@value"),
                "bookerName": bookerName,
                "cottageName": item.get("http://localhost:8080/CottageBookingService/ontology#cottageName", [{}])[0].get("@value"),
                "cottageAddress": item.get("http://localhost:8080/CottageBookingService/ontology#cottageAddress", [{}])[0].get("@value"),
                "bookingStartDate": item.get("http://localhost:8080/CottageBookingService/ontology#bookingStartDate", [{}])[0].get("@value"),
                "bookingEndDate": item.get("http://localhost:8080/CottageBookingService/ontology#bookingEndDate", [{}])[0].get("@value"),
                "actualBedrooms": item.get("http://localhost:8080/CottageBookingService/ontology#actualBedrooms", [{}])[0].get("@value"),
                "actualPlaces": item.get("http://localhost:8080/CottageBookingService/ontology#actualPlaces", [{}])[0].get("@value"),
                "distanceToLake": item.get("http://localhost:8080/CottageBookingService/ontology#actualDistanceToLake", [{}])[0].get("@value"),
                "cottageImage": item.get("http://localhost:8080/CottageBookingService/ontology#cottageImage", [{}])[0].get("@value"),
                "nearestCity": item.get("http://localhost:8080/CottageBookingService/ontology#nearestCity", [{}])[0].get("@value"),
                "distanceToCity": item.get("http://localhost:8080/CottageBookingService/ontology#distanceToCity", [{}])[0].get("@value"),
            }
            formatted_suggestions.append(cottage_data)

    return formatted_suggestions




# {
#         "@id": "_:N4a784a06fc4141e88d273bb1810e229e",
#         "@type": [
#             "http://sswapmeet.sswap.info/sswap/Subject",
#             "http://localhost:8080/CottageBookingService/ontology#Booking"
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#bookerName": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#string",
#                 "@value": "Siaam"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#maxDistanceToCity": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 50
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#maxDistanceToLake": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 100
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#nearestCity": [
#             {
#                 "@id": "http://localhost:8080/CottageBookingService/ontology#City_Helsinki"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#requiredBedrooms": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 3
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#requiredPlaces": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 6
#             }
#         ],
#         "http://sswapmeet.sswap.info/sswap/mapsTo": [
#             {
#                 "@id": "_:Nf8583cf509ac40daa6620c27ac70fa73"
#             }
#         ]
#     },

# {
#         "@id": "_:Nf8583cf509ac40daa6620c27ac70fa73",
#         "@type": [
#             "http://localhost:8080/CottageBookingService/ontology#CottageSuggestion"
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#actualBedrooms": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 3
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#actualDistanceToLake": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 100
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#actualPlaces": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 6
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#bookingEndDate": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#date",
#                 "@value": "2024-12-15"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#bookingNumber": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#string",
#                 "@value": "a7a8e358-e768-4153-9efe-29df4e5b5cc4"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#bookingStartDate": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#date",
#                 "@value": "2024-12-10"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#cottageAddress": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#string",
#                 "@value": "123 Lake Road, Helsinki"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#cottageImage": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#anyURI",
#                 "@value": "https://s3.brilliant.com.bd/images/lakeview.jpg"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#cottageName": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#string",
#                 "@value": "Lakeview Cottage"
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#distanceToCity": [
#             {
#                 "@type": "http://www.w3.org/2001/XMLSchema#integer",
#                 "@value": 50
#             }
#         ],
#         "http://localhost:8080/CottageBookingService/ontology#nearestCity": [
#             {
#                 "@id": "http://localhost:8080/CottageBookingService/ontology#City_Helsinki"
#             }
#         ]
#     },