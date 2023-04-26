import sys
sys.path.insert(0,'../Security')
from encryption import Encryption
from Config import Config
import requests
import json
from datetime import datetime
from Logs import logInfo, logError, logCritical, logWarning


class Log_Server_Interface:
    def __init__(self, config) -> None:
        self.url = config.LOG_SERVER_ADDRESS
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
            "SendTime": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "Publish": publish,
            "Tag": tag
        }
        log_payload = str(log_payload)
        if severity == 'WARNING':
            logWarning(message)
        if severity == 'ERROR':
            logError(message)
        if severity == 'CRITICAL':
            logCritical(message)
        else:
            logInfo(message)
        # encrypt the message
        json_compatible_item_data = self.encryption.encrypt(log_payload)
        response = requests.post(self.url + 'post/log', headers=headers, json=json_compatible_item_data)
        return response.json()


