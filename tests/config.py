import os
import requests

# Store Oauth Token in firebase
firebase_url = os.environ.get('FIREBASE_URL')

# The email that tests should send and retrieve from
EMAIL_ACCOUNT = os.environ.get('EMAIL_ACCOUNT')


def get_access_token():
    r = requests.get(firebase_url)
    response = r.json()
    auth_token = response['access']
    return auth_token

AUTH_TOKEN = get_access_token()
