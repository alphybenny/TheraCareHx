import os

import requests

from dotenv import load_dotenv

# Load .env file
load_dotenv()

BASE_URL = 'https://api.leapoffaith.com/api/service'
BASE_HEADERS = {
    "Content-Type": "application/json"
}


def get_lof_auth_token():
    lof_credentials = {
        "client_id": os.getenv('client_id'),
        "client_secret": os.getenv('client_secret')
    }
    response = requests.post(BASE_URL + '/generate-access-token/', json=lof_credentials, headers=BASE_HEADERS)
    if response.status_code == 200:
        return response.status_code,response.json()['access_token']
    return response.status_code,response.json()['error']

def lof_service_request_headers():
    status_code, lof_auth_token = get_lof_auth_token()
    if status_code == 200:
        return {
            "Content-Type": "application/json",
            "Authorization": "Bearer " + lof_auth_token
        }
    else:
        print(f"Failed to get LoF auth token: {status_code} : {lof_auth_token}")
        raise Exception(f"Failed to get LoF auth token: {status_code}")


class HealthGorillaTokenService:

    def get_bearer_token(self):
        response = requests.post(BASE_URL + '/hg/token/', json={}, headers=lof_service_request_headers())
        if response.status_code == 200:
            return response.json()['access_token']
        else:
            print(f"Failed to get Health Gorilla token: {response.status_code} : {response.json()['message']}")
            raise Exception(f"Failed to get Health Gorilla token: {response.status_code}")

class IMONLPService:

    def tokenize_text(self, text):
        response = requests.post(BASE_URL + '/imo/nlp', json={'text': text}, headers=lof_service_request_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to Retrieve IMO Tokens: {response.status_code} : {response.json()['message']}")
            raise Exception(f"Failed to get Retrieve IMO Tokens: {response.status_code}")

    def getIMO_CoreSearch(self, text, domain=None, session_id=None):
        payload = {'search_term':text, 'domain':domain, 'session_id': session_id}
        response = requests.post(BASE_URL + '/imo/core/search', json=payload, headers=lof_service_request_headers())
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Failed to Retrieve IMO Tokens: {response.status_code} : {response.json()['message']}")
            raise Exception(f"Failed to get Retrieve IMO Tokens: {response.status_code}")
if __name__ == '__main__':
    token = HealthGorillaTokenService().get_bearer_token()
    print('LoF Services verified successfully')