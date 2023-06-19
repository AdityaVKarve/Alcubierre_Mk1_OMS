import datetime
import time
import requests
from encryption import Encryption
import json 
import dropbox

class LOG_Interface:
    def __init__(self, url):
        self.url = url
        self.encryption = Encryption('../Keys/LOG/public_key_.pem', '../Keys/LOG/private_key_.pem')
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

    def get(self, route, config_file=None, encryption=True, access_token=None):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        if config_file is not None:
            route = route + '?config_file=' + config_file
        print(type(access_token))
        response = requests.get(self.url + route, headers=headers, json=access_token)
        # print(response.json())
        # decrypt
        if encryption:
            encrypted_aes_key = response.json()['encrypted_key']
            encrypted_message = response.json()['encrypted_data']
            
            # convert from hex to bytes
            encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
            encrypted_message = bytes.fromhex(encrypted_message)    

            # decrypt
            decrypted_message = self.encryption.decrypt(encrypted_aes_key, encrypted_message)
            # print(decrypted_message)
            # convert string to json
            decrypted_message = decrypted_message.replace("\'", '\"')
            decrypted_message = json.loads(decrypted_message)
            return decrypted_message
        else:
            return response.json()

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
        print(message)
        # encrypt the message
        json_compatible_item_data = self.encryption.encrypt(message)

        if config_file is not None:
            response = requests.post(self.url + route + '?config_file=' + config_file, headers=headers, json=json_compatible_item_data, files=config_file)
        else:
            response = requests.post(self.url + route, headers=headers, json=json_compatible_item_data)
        return response.json()
    
    def get(self, route, config_file=None, encryption=True):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        if config_file is not None:
            route = route + '?config_file=' + config_file
        response = requests.get(self.url + route, headers=headers)
        # print(response.json())
        # decrypt
        if encryption:
            encrypted_aes_key = response.json()['encrypted_key']
            encrypted_message = response.json()['encrypted_data']
            
            # convert from hex to bytes
            encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
            encrypted_message = bytes.fromhex(encrypted_message)    

            # decrypt
            decrypted_message = self.encryption.decrypt(encrypted_aes_key, encrypted_message)
            # print(decrypted_message)
            # convert string to json
            decrypted_message = decrypted_message.replace("\'", '\"')
            decrypted_message = json.loads(decrypted_message)
            return decrypted_message
        else:
            return response.json()



class ADS_Interface:
    def __init__(self, url):
        self.url = url
        self.get_routes = ['get/user_data', 'get/spreads', 'get/config']
        self.post_routes = ['post/user_data', 'post/spreads', 'post/config']
        self.encryption = Encryption('../Keys/ADS/public_key.pem', '../Keys/ADS/private_key.pem')
        # self.token = self.authentification()
        self.token = ""

    def authentification(self):
        username = 'vishal'
        password = 'vishal'

        data = {
            'username': username,
            'password': password
        }

        response = requests.post(self.url + 'token', data=data)
        print(response.json())
        token = response.json()['access_token']
        return token

    def get(self, route, data=None, encryption=True):
        headers = {
            'Authorization': 'Bearer ' + self.token
        }
        response = requests.get(self.url + route, headers=headers, json=data)
        # print(response.json())

        if encryption:
            encrypted_aes_key = response.json()['encrypted_key']
            encrypted_message = response.json()['encrypted_data']
            # convert from hex to bytes
            encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
            encrypted_message = bytes.fromhex(encrypted_message)
            # print(encrypted_aes_key)
            # print(encrypted_message) 
            # decrypt
            message = self.encryption.decrypt(encrypted_aes_key, encrypted_message)
            # print(message)
        
            return message
        else:
            return response.json()

        

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


if __name__ == '__main__':
    # URL of the ADS server
    # DEV
    # url = 'http://localhost:8080/'
    # url = 'http://13.233.26.147:9000/'
    # PROD
    # url = 'http://15.207.12.225:8080/'
    # url = 'http://15.207.12.225:6000/'


    # Message to be sent to ADS as a payload
    # message = {
    # "fin_user_1": {
    #     "USER_TYPE": "ZERODHA",
    #     "PAPER_TRADE": "True",
    #     "LOGIN_DETAILS": {
    #         "API_KEY": "wd4rw474uonpvn94",
    #         "API_SECRET": "8bsd661b6i29y064pei4riikj0lr3ede",
    #         "ID": "WG5235",
    #         "PASSWORD": "Finvant@Research1",
    #         "TOTP_PIN": "BK4I753O24NO5BU5JLTO2JPT2TFT54CC"
    #     },
    #     "STRATEGY_DETAILS": {
    #         "NOVA": {
    #             "NIFTY": [
    #                 0,
    #                 1
    #             ],
    #             "BANKNIFTY": [
    #                 0,
    #                 1
    #             ],
    #             "SPREAD_TEST": [
    #                 1,
    #                 0
    #             ],
    #             "NIFTY_SYNTHETIC_INTRADAY_LONG": [
    #                 1,
    #                 0
    #             ],
    #             "NIFTY_SYNTHETIC_INTRADAY_SHORT": [
    #                 1,
    #                 0
    #             ],
    #             "BANKNIFTY_SYNTHETIC_INTRADAY_LONG": [
    #                 1,
    #                 0
    #             ],
    #             "BANKNIFTY_SYNTHETIC_INTRADAY_SHORT": [
    #                 1,
    #                 0
    #             ]
    #         }
    #     }
    # }
    # }
    # print(message)
    
    # spreads = {
    #     "SPREAD_TEST": {
    #         "BUY":[
    #                 "NIFTY|L|200|PE|MONTH|0|1|0|0",
    #                 "NIFTY|G|200|PE|MONTH|0|0|0|0"
    #         ],
    #         "OPEN SHORT":[
    #                 "NIFTY|L|100|PE|MONTH|0|1|0|1",
    #                 "NIFTY|G|100|PE|MONTH|0|0|0|0"
    #         ]
    #     },
    #         "NIFTY_SYNTHETIC_INTRADAY_LONG": {
    #         "INDEX_PEG":"NIFTY",
    #         "BUY":[
    #             "NIFTY|L|0|CE|WEEK|0|0|0|0"
    #         ],
    #         "OPEN SHORT":[
    #             "NIFTY|L|0|PE|WEEK|0|0|0|0"
    #         ]
    #     },
    #     "NIFTY_SYNTHETIC_INTRADAY_SHORT": {
    #         "INDEX_PEG":"NIFTY",
    #         "BUY":[
    #             "NIFTY|L|0|PE|WEEK|0|0|0|0"
    #         ],
    #         "OPEN SHORT":[
    #             "NIFTY|L|0|CE|WEEK|0|0|0|0"
    #         ]
    #     },
    #         "BANKNIFTY_SYNTHETIC_INTRADAY_LONG": {
    #         "INDEX_PEG":"BANKNIFTY",
    #         "BUY":[
    #             "BANKNIFTY|L|0|CE|WEEK|0|0|0|0"
    #         ],
    #         "OPEN SHORT":[
    #             "BANKNIFTY|L|0|PE|WEEK|0|0|0|0"
    #         ]
    #     },
    #     "BANKNIFTY_SYNTHETIC_INTRADAY_SHORT": {
    #         "INDEX_PEG":"BANKNIFTY",
    #         "BUY":[
    #             "BANKNIFTY|L|0|PE|WEEK|0|0|0|0"
    #         ],
    #         "OPEN SHORT":[
    #             "BANKNIFTY|L|0|CE|WEEK|0|0|0|0"
    #         ]
    #     }
    # }
    
    ########## ADS INTERFACE ##########
    # Initialize the ADS interface
    # interface = ADS_Interface(url)

    # Uncomment the following lines to test the ADS POST requests
    # print(interface.post('post/user_data', str(message)))

    # Uncomment the following lines to test the ADS GET requests
    # print(interface.get('get/user_data'))
    # print(interface.get('get/trading_day?date=2023-12-25'))
    # time = '2023-05-09_14:47:42'
    # instrument = 'NIFTY'
    # nomenclature = 'NIFY23JUNFUT'
    # price = 18369.0
    # position = 'BUY'

    # data = [
    #     {
    #         'end_date': '2023-05-09_14:47:42',
    #         'instrument_nomenclature': 'NIFTY',
    #         'trading_symbol':'NIFY23JUNFUT',
    #         'price': 18169.0,
    #         'position': 'BUY'
    #     }
    # ]
    # print(interface.get('candlestick/', data=data, encryption=False))
    # print(interface.get('get/candlestick/2023-05-09_14:47:42/NIFTY/NIFY23JUNFUT/18369.0'))
    # print(interface.get('get/spreads'))
    # print(interface.get('get/config?config_file=LOG')) # set config_file to LOG, DATASERVER, or OMS
    ########## ADS INTERFACE ##########


    # Message to be sent to LOG as a payload
    # import datetime
    log = {
            "Section": "Test",
            "Severity": "INFO",
            "Message": "This is a test log via API",
            "SendTime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Publish": 1,
            "Tag" : "OMSMB"
        }
    
    # URL of the LOG server
    # DEV
    url = 'http://localhost:9092/'
    # PROD
    # url = 'http://15.207.12.225:9092/'
    
    ########## LOG INTERFACE ##########

    
    # Initialize the LOG interface
    interface = LOG_Interface(url)

    # Uncomment the following lines to test the LOG POST requests
    for i in range(10):
        print(interface.post('post/log', str(log)))
    
    
    ### ARCHIVE
    # Generate a new access token
    # auth_flow = dropbox.DropboxOAuth2FlowNoRedirect("0g6qmdwim30e13x", "9k0kbbenkalk5bo")
    # authorize_url = auth_flow.start()
    # print("1. Go to: " + authorize_url)
    # print("2. Click \"Allow\" (you might have to log in first)")
    # print("3. Copy the authorization code.")
    # auth_code = input("Enter the authorization code here: ").strip()
    # result = auth_flow.finish(auth_code)
    # access_token = result.access_token
    # access_token = {'access_token': access_token}
    # print("Access token: " + str(access_token))
    # print(interface.get('get/archive_logs', encryption=False, access_token=access_token))
    
    # Uncomment the following lines to test the LOG GET requests
    # print(interface.get('get/log?condition=All'))
    # pretty priny logs
    # print(json.dumps(interface.get('get/log?condition=All'), indent=4, sort_keys=True))
    # print(interface.get('get/log?condition=severity&value=INFO')) # set condition to Publish, Severity, Date or Section and value for the condition
    ########## LOG INTERFACE ##########
    


    # order_1 = {
    #     "ORDERS":[
    #         {
    #             "STRATEGY": "QUASAR_5M_FUTURES",
    #             "INSTRUMENT_NOMENCLATURE": "NIFTY",
    #             "POSITION":"OPEN SHORT",
    #             "TARGET":0,
    #             "STOPLOSS":0 
    #         }
    #     ]
    # }
    # order_2 = {
    #     "ORDERS":[
    #         {
    #             "STRATEGY": "NOVA",
    #             "INSTRUMENT_NOMENCLATURE": "NIFTY",
    #             "POSITION":"SELL",
    #             "TARGET":0,
    #             "STOPLOSS":0 
    #         }
    #     ]
    # }

    # order = {'ORDERS': [{'STRATEGY': 'QUASAR_5M', 'INSTRUMENT_NOMENCLATURE': 'BANKNIFTY_SYNTHETIC_INTRADAY_SHORT', 'POSITION': 'SELL', 'TARGET': 0, 'STOPLOSS': 0.5}]}
    # # order = {'ORDERS': [{'STRATEGY': 'QUASAR_5M', 'INSTRUMENT_NOMENCLATURE': 'NIFTY_SYNTHETIC_INTRADAY_SHORT', 'POSITION': 'SELL', 'TARGET': 0, 'STOPLOSS': 0}]}
    # order = {'ORDERS': [{'STRATEGY': 'OPHIUCUS', 'INSTRUMENT_NOMENCLATURE': 'NIFTY|L|0|PE|WEEK|0', 'POSITION': 'OPEN SHORT', 'TARGET': 0, 'STOPLOSS': 0}, {'STRATEGY': 'QUASAR_5M', 'INSTRUMENT_NOMENCLATURE': 'NIFTY_SYNTHETIC_INTRADAY_SHORT', 'POSITION': 'BUY', 'TARGET': 0, 'STOPLOSS': 0.5}]}
    # # # URL of the LOG server
    # # # DEV
    # url = 'http://localhost:9093/'
    # # # # PROD
    # url = 'http://15.207.12.225:9093/'
    # url = 'http://13.127.242.54:9093/'
    # # # ########## OMS INTERFACE ##########
    # # # # Initialize the OMS interface
    # interface = OMS_Interface(url)
    # # # # # # Uncomment the following lines to test the OMS POST requests
    # results = interface.post('orders/create', order_2)
    # for result in results:
    #     print(result, results[result])
    # rollover_result = interface.post('orders/rollover', order)
    # print(rollover_result)

    # for i in range (200):
    #     if i%2 == 0:
    #         print('order 1')
    #         results = interface.post('orders/create', order_1)
    #         for result in results:
    #             print(result, results[result])
    #     else:
    #         print('order 2')
    #         results = interface.post('orders/create', order_2)
    #         for result in results:
    #             print(result, results[result])
    #     time.sleep(7)
    ########## OMS INTERFACE ##########

    

    # message = {'encrypted_key': '90941e286ea78d54e9f45a9b92c05cd50f33fd72eb38b3599c4ba69a7c1a6c0e09de9532bab8843537f59b3108b3eead538fa6bb51d29f490d01839790e79f866e2845ef21e370b9cec3e893711adf85e4ceeec9c3c08af5143f48e2a035ec3811be54c0a387faf9bb1b5bda9b1752ad8e7eee0f4bac9f33d046979c258ad92417e4ee4f1ea8b98c4f99e85560b9f97d3aa59c383943fbe929779b78e683b33e0f401279c9f3307858a38ba65897b2306ee2367a3984bd4945859eee8187d5617589eb9e6af246ad6c23f5c2c81d72987590c402f1b83997a99ba8dbd571ed0e564fa8ae4267f222ea414b7cab855096a6d4756503b9a9cf5b7ae442edb5caf0', 'encrypted_data': '674141414141426a3666474a345f4d316f4d4f4938732d5a306c50316966436a373143684c6d4e58505f4d49515f58514b7845777a79684f612d73705937574b5f6a787a57777732746739556e6f6675586b4c2d57383774687457354e4a74414a3742786273516c386c3450547544674b6c3035706c6a4d337a543438706d51374b3147374d4c6b4d2d6361775f41596e6e6e612d73475a3543316d78394e6547575f4c32374f575138514f4c4e31762d68484b56504c4e5078747978686f716f484f5a50425974464d473632655352442d7656386132473166704939552d4a75364e5647746c67445131576f4135477a477a736e3273394f504355787332454177393039686a365a324f4a'}
    # # Decrypt the message
    # encryption = Encryption('../Keys/OMS/public_key_.pem', '../Keys/OMS/private_key_.pem')
    # encrypted_aes_key = message['encrypted_key']
    # encrypted_message = message['encrypted_data']
    # # convert from hex to bytes
    # encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
    # encrypted_message = bytes.fromhex(encrypted_message)
    # # print(encrypted_aes_key)
    # # print(encrypted_message) 
    # # decrypt
    # message = encryption.decrypt(encrypted_aes_key, encrypted_message)  
    # print(message)  
