import sys
sys.path.insert(0,'../Security')
from encryption import Encryption
import requests
import json
from datetime import datetime
from Config import Config


class Log_Server_Interface:
    def __init__(self, config:Config) -> None:
        self.url = config.LOG_SERVER_ADRESS
        self.subsystem = config.SUBSYSTEMS
        self.encryption = Encryption('../Security/Keys/LOG/public_key_.pem', '../Keys/LOG/private_key_.pem')
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
    
    def postLog(self, severity, message, publish, tag = ''):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        
        log_payload = {
            "Section":self.subsystem,
            "Severity":severity,
            "Message":message,
            "Send Time": datetime.now(),
            "Publish": publish  
        }
        # encrypt the message
        json_compatible_item_data = self.encryption.encrypt(log_payload)
        response = requests.post(self.url + 'post/log', headers=headers, json=json_compatible_item_data)
        return response.json()