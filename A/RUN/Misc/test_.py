import base64
import requests

import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.fernet import Fernet

from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse

# Hosting url
url = 'http://15.207.12.225:8080/'
# Developement url
# url = 'http://localhost:8000/'

# Get route
# url_ = url + 'get/user_data'
# Post route
# url_post = url + 'post/user_data'

get_routes = ['get/user_data', 'get/spreads', 'get/config']
post_routes = ['post/user_data', 'post/spreads', 'post/config']


########## TESTING FUNCTIONS ##########
def test_get():
    for route in get_routes:
        if route == 'get/config':
            get(url + route, 'LOG')
        else:
            get(url + route)


def test_post(message):
    for route in post_routes:
        if route == 'post/config':
            encrypt(message, url + route, 'LOG')
        else:
            encrypt(message, url + route)



######### HELPER FUNCTIONS #########
def authentification():
    username = 'vishal'
    password = 'vishal'

    data = {
        'username': username,
        'password': password
    }

    response = requests.post(url + 'token', data=data)
    token = response.json()['access_token']
    return token

def get(url, config_file=None):
    token = authentification()
    headers = {
        'Authorization': 'Bearer ' + token
    }
    if config_file is not None:
        url = url + '?config_file=' + config_file
    response = requests.get(url, headers=headers)
    print(response)
    # decrypt
    encrypted_aes_key = response.json()['encrypted_key']
    encrypted_message = response.json()['encrypted_data']
    # convert from hex to bytes
    encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
    encrypted_message = bytes.fromhex(encrypted_message)    

    # decrypt
    decrypted_message = decrypt(encrypted_aes_key, encrypted_message)
    print(decrypted_message)




def encrypt(message, url, config_file=None):
    """ Encrypt a message using hybrid encryption (RSA + AES). """
    ## Generate a random AES key
    with open('../Keys/public_key_.pem', 'rb') as f:
        public_key = serialization.load_pem_public_key(
            f.read(),
            backend=default_backend()
        )
    aes_key = Fernet.generate_key()
    ## Encrypt the AES key with RSA
    encrypted_aes_key = public_key.encrypt(
        aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    ## Encrypt the message with AES
    f = Fernet(aes_key)
    encrypted_message = f.encrypt(message.encode('utf-8'))

    # POST FORMATTING
    # convert to hex format
    encrypted_key = encrypted_aes_key.hex()
    encrypted_data = encrypted_message.hex()
    # Package encrypted key and encrypted user data into a dictionary
    response = {
        "encrypted_key": str(encrypted_key),
        "encrypted_data": str(encrypted_data),
    }
    # Encode response to json serializable object for api return
    json_compatible_item_data = jsonable_encoder(
        response, custom_encoder={bytes: lambda v: v.decode("utf-8")}
    )

    print(type(json_compatible_item_data['encrypted_key']))
    post(json_compatible_item_data, url, config_file)

def post(response_, url, config_file=None):
    token = authentification()
    headers = {
        'Authorization': 'Bearer ' + token
    }

    if config_file is not None:
        url = url + '?config_file=' + config_file
    
    response = requests.post(url, headers=headers, json=response_)
    print(response.json())



def decrypt(encrypted_aes_key, encrypted_message):
    """ Decrypt a message using hybrid encryption (RSA + AES). """
    ## Decrypt the AES key with RSA
    with open('../Keys/private_key_.pem', 'rb') as f:
        private_key = serialization.load_pem_private_key(
            f.read(),
            password=None,
            backend=default_backend()
        )
    aes_key = private_key.decrypt(
        encrypted_aes_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )
    ## Decrypt the message with AES
    f = Fernet(aes_key)
    decrypted_message = f.decrypt(encrypted_message).decode('utf-8')
    ## Return the decrypted message
    return decrypted_message
######### HELPER FUNCTIONS #########


message = {
    "FINVANT": {
        "API_TYPE": "ODVIN",
        "API_LOGIN_CREDS": {
            "KEY": 1234
        },
        "STRATEGY_ALLOCATIONS": {
            "NIFTY": 0.5,
            "BANKNIFTY": 0.5
        }
    }
}

message_3 = {
    "SUB_SYSTEM": "LOG_",
    "TELEGRAM_TOKEN": "1514947310:AAGM4EkoO9Qs6G0e2E6V2afEbmm-FnzH700",
    "TELEGRAM_GENERAL_CHATID": "-685186089",
    "TELEGRAM_ERROR_CHATID": "-724410691",
    "KAFKA_SUB_TOPIC": "log",
    "KAFKA_CONSUMER_GROUP": "log_server",
    "KAFKA_SERVER_ADDRESS": "15.207.12.225:9092"
}

message_2 = {
    "name": "LongStrangleATMWeekly",
    "leg_count": 2,
    "legs": {
      "Leg 5": {
        "STRIKE": 0,
        "TYPE": "CE",
        "TARGET_TYPE": "NA",
        "SL_TYPE": "NA",
        "SL": 0,
        "EXPIRY TYPE": "WEEKLY",
        "EXPIRY_LOOKAHEAD": 0
      },
      "Leg 6": {
        "STRIKE": 0,
        "TYPE": "CE",
        "TARGET_TYPE": "NA",
        "SL_TYPE": "NA",
        "SL": 0,
        "EXPIRY TYPE": "WEEKLY",
        "EXPIRY_LOOKAHEAD": 0
      }
    }
}

message_list = [message, message_2, message_3]


############## MAIN ##############
## Uncomment to tet the POST method
# encrypt(str(message), url+'post/user_data')
## Uncomment to test the GET method
get()

## Uncomment to test all GET methods
# test_get()
## Uncomment to test all POST methods
# test_post(str(message))
# for message in message_list:
#     test_post(str(message))
############## MAIN ##############
