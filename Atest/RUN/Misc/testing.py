import base64
import requests

import json
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding

import time
import datetime
import numpy as np

class APITESTER:
    def __init__(self):
        self.url_dev = 'http://localhost:8000/'
        self.url_prod = 'http://15.207.12.225:8080/'
        self.url = self.url_prod

        self.url_get_ud = self.url_prod + 'get/user_data'
        self.url_post_ud = self.url_prod + 'post/user_data'

        self.header = {}

    
    def authentification(self):
        username = 'vishal'
        password = 'vishal'

        data = {
            'username': username,
            'password': password
        }

        response = requests.post(self.url + 'token', data=data)
        # token = response.json()['access_token']
        self.header = {
            'Authorization': 'Bearer ' + response.json()['access_token']
        }
        # return token
    
    def encrypt(self, message=None):
        """ Encrypt the message to be sent to the server. """

        with open('../Keys/public_key.pem', 'rb') as f:
            public_key_pem = serialization.load_pem_public_key(
                f.read(),
                backend=default_backend()
            )

        if message is None:
            message_json = {
                "message" : {
                    "FINVANT": {
                        "API_TYPE": "ODIN",
                        "API_LOGIN_CREDS": {
                            "KEY": 1234
                        },
                        "STRATEGY_ALLOCATIONS": {
                            "NIFTY": 0.5,
                            "BANKNIFTY": 0.5
                        }
                    }
                }
            }
        else:
            message_json = message


        message = json.dumps(message_json).encode('utf-8')
        encrypted_message = public_key_pem.encrypt(
            message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        encrypted_message = base64.b64encode(encrypted_message)
        # self.post(encrypted_message)
        return encrypted_message


    def decrypt(self, message):
        """ Decrypt the message returned from the server. """
        
        with open('../Keys/private_key.pem', 'rb') as f:
            private_key_pem = serialization.load_pem_private_key(
                f.read(),
                password=None,
                backend=default_backend()
            )
        
        encrypted_message = message
        decrypted_message = private_key_pem.decrypt(
            encrypted_message,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )

        message = decrypted_message.decode('utf-8')
        message_json = json.loads(message)
        # print(json.dumps(message_json, indent=4, sort_keys=True))
        return message_json

    def get(self):

        if self.header == {}:
            self.authentification()
        # token = self.authentification()
        headers = self.header
        response = requests.get(self.url_get_ud, headers=headers)
        

        message = response.json()['message']
        message = base64.b64decode(message)
        message = self.decrypt(message)

        return message

    def post(self, message):
        if self.header == {}:
            self.authentification()
        # token = self.authentification()
        headers = self.header

        encrypted_message = self.encrypt(message)
        
        data = {
            'data': encrypted_message
        }
        response = requests.post(self.url_post_udurl_post, headers=headers, json=data)
        # print(response.json())
        return response.json()

    def test_post(self):
        """ Test API POST request latency and throughput. """
        print('Testing POST')
        

        message = {
            "message" : {
                "FINVANT": {
                    "API_TYPE": "ODIN",
                    "API_LOGIN_CREDS": {
                        "KEY": 1234
                    },
                    "STRATEGY_ALLOCATIONS": {
                        "NIFTY": 0.5,
                        "BANKNIFTY": 0.5
                    }
                }
            }
        }

        start_time = time.gmtime(0)
        for i in range(100):
            self.post(message)
        end_time = time.gmtime(0)

        print('Time taken: ', end_time - start_time)
        print('Throughput: ', 100/(end_time - start_time))
        print('Latency: ', (end_time - start_time)/100)

    def test_get(self):
        """ Test API GET request latency and throughput using epoch time. """
        print('Testing GET')

        start_time = datetime.datetime.now().strftime('%s')
        for i in range(100):
            self.get()
        end_time = datetime.datetime.now().strftime('%s')
        print('Time taken: ', int(end_time) - int(start_time))
        print('Throughput: ', 100/(int(end_time) - int(start_time)))
        print('Latency: ', (int(end_time) - int(start_time))/100)






######## MAIN ########
if __name__ == '__main__':
    api = APITESTER()
    # api.test_post() # Test POST request latency and throughput
    api.test_get() # Test GET request latency and throughput

######## MAIN ########