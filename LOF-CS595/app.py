from flask import Flask, jsonify, request
import requests
import sys
import os

# Make HealthGorillaTokenService accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), './../..')))
from lof.services import HealthGorillaTokenService
from lof.services import IMONLPService

app = Flask(__name__)
BASE_URL = "https://sandbox.healthgorilla.com/fhir"

def get_bearer_token():
    token_service = HealthGorillaTokenService()
    return token_service.get_bearer_token()

def fetch_resource(resource_type, patient_id):
    try:
        token = get_bearer_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{BASE_URL}/{resource_type}?patient={patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

@app.route("/search", methods=["GET"])
def search_patient():
    given = request.args.get("given")
    family = request.args.get("family")
    birthdate = request.args.get("birthdate")

    if not (given and family):
        return jsonify({"error": "Missing required query params: 'given' and 'family'"}), 400

    try:
        token = get_bearer_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        url = f"{BASE_URL}/Patient?given={given}&family={family}"
        if birthdate:
            url += f"&birthdate={birthdate}"

        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

        simplified = []
        for entry in data.get("entry", []):
            resource = entry.get("resource", {})
            pid = resource.get("id", "")
            name_info = resource.get("name", [{}])[0]
            full_name = " ".join(name_info.get("given", [])) + " " + name_info.get("family", "")
            dob = resource.get("birthDate", "")
            gender = resource.get("gender", "")
            simplified.append({
                "id": pid,
                "name": full_name.strip(),
                "dob": dob,
                "gender": gender
            })

        return jsonify({"count": len(simplified), "patients": simplified})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/patient/<patient_id>", methods=["GET"])
def get_patient(patient_id):
    try:
        token = get_bearer_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        url = f"{BASE_URL}/Patient/{patient_id}"
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ⬇️ Resource endpoints
@app.route("/conditions/<patient_id>", methods=["GET"])
def get_conditions(patient_id):
    return jsonify(fetch_resource("Condition", patient_id))

@app.route("/allergies/<patient_id>", methods=["GET"])
def get_allergies(patient_id):
    return jsonify(fetch_resource("AllergyIntolerance", patient_id))

@app.route("/medications/<patient_id>", methods=["GET"])
def get_medications(patient_id):
    return jsonify(fetch_resource("MedicationRequest", patient_id))

@app.route("/immunizations/<patient_id>", methods=["GET"])
def get_immunizations(patient_id):
    return jsonify(fetch_resource("Immunization", patient_id))

@app.route("/procedures/<patient_id>", methods=["GET"])
def get_procedures(patient_id):
    return jsonify(fetch_resource("Procedure", patient_id))

@app.route("/family-history/<patient_id>", methods=["GET"])
def get_family_history(patient_id):
    return jsonify(fetch_resource("FamilyMemberHistory", patient_id))


@app.route("/imo-core-search", methods=["GET"])
def imo_core_search():
    try:
        text = request.args.get("text")
        domain = request.args.get("domain", "condition")  # Default to "condition" if not provided

        if not text:
            return jsonify({"error": "Missing 'text' query parameter"}), 400

        NLPService = IMONLPService()
        result = NLPService.getIMO_CoreSearch(text=text, domain=domain)

        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500





def extract_medical_codes_from_text(text: str):
    try:
        response = IMONLPService().tokenize_text(text=text)
        results = []
        valid_semantics = ['problem', 'drug', 'treatment', 'imo_procedure', 'test']

        for entity in response.get("entities", []):
            if entity.get("semantic") not in valid_semantics:
                continue

            entity_info = {
                "text": entity.get("text", ""),
                "semantic_type": entity.get("semantic", ""),
                "assertion": entity.get("assertion", ""),
                "codes": {}
            }

            codemaps = entity.get("codemaps", {})
            for system, mapping in codemaps.items():
                if system == "imo":
                    entity_info["codes"]["imo"] = mapping.get("lexical_code", "")
                elif "codes" in mapping and mapping["codes"]:
                    if system == "rxnorm":
                        entity_info["codes"]["rxnorm"] = mapping["codes"][0].get("rxnorm_code", "")
                    else:
                        entity_info["codes"][system] = mapping["codes"][0].get("code", "")
            results.append(entity_info)
        return results
    except Exception as e:
        return {"error": str(e)}

@app.route("/tokenize-medical", methods=["GET", "POST"])
def tokenize_medical():
    try:
        if request.method == "GET":
            text = request.args.get("text", "")
        elif request.is_json:
            data = request.get_json()
            text = data.get("text", "")
        else:
            text = request.form.get("text", "")

        if not text:
            return jsonify({"error": "Missing 'text'"}), 400

        result = extract_medical_codes_from_text(text)
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True)
