from Logs import logCritical, logInfo
from Config import Config
import json
import requests
# from Security.encryption import Encryption
import sys
# sys.path.append('..')
import sys
sys.path.insert(0, '../Security')
from encryption import Encryption

class ADS_Interface:
    def __init__(self):
        self.url = Config().ADS_SERVER_ADDRESS
        self.get_routes = ['get/user_data', 'get/spreads', 'get/config']
        self.post_routes = ['post/user_data', 'post/spreads', 'post/config']
        self.encryption = Encryption(
            '../Security/Keys/ADS/public_key.pem', '../Security/Keys/ADS/private_key.pem')
        self.token = self.authentification()

    def authentification(self):
        try:
            username = 'vishal'
            password = 'vishal'

            data = {
                'username': username,
                'password': password
            }

            response = requests.post(self.url + 'token', data=data)
            token = response.json()['access_token']
            return token
        except:
            logCritical('OMSB_ADSINT_1', exit=True)

    def get(self, route):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        response = requests.get(self.url + route, headers=headers)
        encrypted_aes_key = response.json()['encrypted_key']
        encrypted_message = response.json()['encrypted_data']
        # convert from hex to bytes
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
        encrypted_message = bytes.fromhex(encrypted_message)
        # decrypt
        message = self.encryption.decrypt(encrypted_aes_key, encrypted_message)
        return message

    def get_user_data(self):
        try:
            return json.loads(self.get('get/user_data'))
        except:
            logCritical('OMSB_ADSINT_2', exit=True)

    def get_spreads(self):
        try:
            return json.loads(self.get('get/spreads'))
        except:
            logCritical('OMSB_ADSINT_3', exit=True)

    def update_config(self):
        print("print")
        try:
            with open('../Config/OMS_Backend_Config.json', 'w') as f:
                json.dump(json.loads(
                    self.get('get/config?config_file=OMS')), f, indent=2)
        except:
            logCritical('OMSB_ADSINT_4', exit=True)
