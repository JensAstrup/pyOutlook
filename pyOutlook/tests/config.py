import os
import requests

# Store Oauth Token in firebase
firebase_url = os.environ.get('FIREBASE_URL')

r = requests.get(firebase_url)
response = r.json()
AUTH_TOKEN = response['access']

# The email that tests should send and retrieve from
EMAIL_ACCOUNT = os.environ.get('EMAIL_ACCOUNT')
