import sys
sys.path.insert(0,'../Security')
from encryption import Encryption
import requests

class OMS_Interface:
    def __init__(self, url):
        self.url = url
        self.get_routes = []
        self.post_routes = ['orders/create']
        self.encryption = Encryption('../Keys/OMS/public_key_.pem', '../Keys/OMS/private_key_.pem')
        self.token = self.authentification()

    def authentification(self):
        username = 'vishal'
        password = 'vishal'

        data = {
            'username': username,
            'password': password
        }

        response = requests.post(self.url + 'token', data=data)
        token = response.json()['access_token']
        return token

    def post(self, route, message, config_file=None):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        # encrypt the message
        json_compatible_item_data = self.encryption.encrypt(message)

        if config_file is not None:
            response = requests.post(self.url + route + '?config_file=' + config_file, headers=headers, json=json_compatible_item_data, files=config_file)
        else:
            response = requests.post(self.url + route, headers=headers, json=json_compatible_item_data)
        return response.json()
    
    def get_instrument_details(self,instrument_nomenclature:str):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        response = requests.get(self.url + 'instrument/{}'.format(instrument_nomenclature), headers=headers)
        return response.json()


    

