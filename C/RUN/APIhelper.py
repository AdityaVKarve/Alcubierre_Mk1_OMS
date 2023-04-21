import requests
from APIencryption import Encryption
import json 

class LOG_Interface:
    def __init__(self, url):
        """ 
        This function is used to initialize the LOG_Interface class.

        Parameters
        ----------
        url : str
            The url to the LOG server.

        Returns
        -------
        None

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        self.url = url
        self.encryption = Encryption('../Keys/LOG/public_key_.pem', '../Keys/LOG/private_key_.pem')
        self.token = self.authentification()

    def authentification(self):
        """ 
        This function is used to get a token from the LOG server.

        Parameters
        ----------
        None

        Returns
        -------
        str
            The token.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        username = 'vishal'
        password = 'vishal'

        data = {
            'username': username,
            'password': password
        }

        response = requests.post(self.url + 'token', data=data)
        token = response.json()['access_token']
        return token

    def get(self, route, config_file=None):
        """ 
        This function is used to get data from the LOG server.
        
        Parameters
        ----------
        route : str
            The route to the LOG server.
        config_file : str
            The path to the config file.

        Returns
        -------
        dict
            The decrypted message.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        try:
            headers = {
                'Authorization': 'Bearer ' + self.token
            }
            if config_file is not None:
                route = route + '?config_file=' + config_file
            response = requests.get(self.url + route, headers=headers)
        except Exception as e:
            # Possible error: Token expired -> login again to get new token
            self.token = self.authentification()
            self.get(route, config_file)
            return
        # decrypt
        encrypted_aes_key = response.json()['encrypted_key']
        encrypted_message = response.json()['encrypted_data']
        
        # convert from hex to bytes
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
        encrypted_message = bytes.fromhex(encrypted_message)    

        # decrypt
        decrypted_message = self.encryption.decrypt(encrypted_aes_key, encrypted_message)
        
        # convert string to json
        decrypted_message = decrypted_message.replace("\'", '\"')
        decrypted_message = json.loads(decrypted_message)
        return decrypted_message

    def post(self, route, message, config_file=None):
        """ 
        This function is used to post data to the LOG server.

        Parameters
        ----------
        route : str
            The route to the LOG server.
        message : dict
            The message to be sent.
        config_file : str
            The path to the config file.

        Returns
        -------
        dict
            The response from the LOG server.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        try:
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
        except Exception as e:
            # Possible error: Token expired -> login again to get new token
            self.token = self.authentification()
            self.post(route, message, config_file)


class ADS_Interface:
    def __init__(self, url):
        """ 
        This function is used to initialize the ADS_Interface class.

        Parameters
        ----------
        url : str
            The url to the ADS server.

        Returns
        -------
        None

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        self.url = url
        self.get_routes = ['get/user_data', 'get/spreads', 'get/config']
        self.post_routes = ['post/user_data', 'post/spreads', 'post/config']
        self.encryption = Encryption('../Keys/ADS/public_key.pem', '../Keys/ADS/private_key.pem')
        self.token = self.authentification()
        self.headers = {
            "Authorization": "Bearer " + self.token
        }

    def authentification(self):
        """ 
        This function is used to get a token from the ADS server.

        Parameters
        ----------
        None

        Returns
        -------
        str
            The token.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        username = 'vishal'
        password = 'vishal'

        data = {
            'username': username,
            'password': password
        }

        response = requests.post(self.url + 'token', data=data)
        token = response.json()['access_token']
        return token

    def get(self, route):
        """ 
        This function is used to get data from the ADS server.
        
        Parameters
        ----------
        route : str
            The route to the ADS server.
        config_file : str
            The path to the config file.

        Returns
        -------
        dict
            The decrypted message.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        try:
            headers = self.headers
            response = requests.get(self.url + route, headers=headers)
        except Exception as e:
            # Possible error: Token expired -> login again to get new token
            self.token = self.authentification()
            self.headers = {
                'Authorization': 'Bearer ' + self.token
            }
            self.get(route)
            return
        encrypted_aes_key = response.json()['encrypted_key']
        encrypted_message = response.json()['encrypted_data']
        # convert from hex to bytes
        encrypted_aes_key = bytes.fromhex(encrypted_aes_key)
        encrypted_message = bytes.fromhex(encrypted_message)
        # decrypt
        message = self.encryption.decrypt(encrypted_aes_key, encrypted_message)
        return message

    def get_spreads(self):
        """ 
        This function is used to get spreads from the ADS server.

        Parameters
        ----------
        None

        Returns
        -------
        dict
            The decrypted message.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        return json.loads(self.get('get/spreads'))

        

    def post(self, route, message, config_file=None):
        """ 
        This function is used to post data to the ADS server.

        Parameters
        ----------
        route : str
            The route to the ADS server.
        message : dict
            The message to be sent.
        config_file : str
            The path to the config file.

        Returns
        -------
        dict
            The response from the ADS server.

        Keyword Arguments
        -----------------
        None

        Raises
        ------
        None
        """
        try:
            headers = self.headers
            # encrypt the message
            json_compatible_item_data = self.encryption.encrypt(message)

            if config_file is not None:
                response = requests.post(self.url + route + '?config_file=' + config_file, headers=headers, json=json_compatible_item_data, files=config_file)
            else:
                response = requests.post(self.url + route, headers=headers, json=json_compatible_item_data)
            return response.json()
        except Exception as e:
            # Possible error: Token expired -> login again to get new token
            self.token = self.authentification()
            self.headers = {
                'Authorization': 'Bearer ' + self.token
            }
            self.post(route, message, config_file)
            return


if __name__ == '__main__':
    # URL of the ADS server
    # DEV
    # url = 'http://localhost:8000/'
    # PROD
    # url = 'http://15.207.12.225:8080/'


    # Message to be sent to ADS as a payload
    # message = {
    #     "FINVANT": {
    #         "API_TYPE": "ODIN",
    #         "API_LOGIN_CREDS": {
    #             "KEY": 1234
    #         },
    #         "STRATEGY_ALLOCATIONS": {
    #             "NIFTY": 0.5,
    #             "BANKNIFTY": 0.5
    #         }
    #     }
    # }
    
    
    ########## ADS INTERFACE ##########
    # Initialize the ADS interface
    # interface = ADS_Interface(url)

    # Uncomment the following lines to test the ADS POST requests
    # print(interface.post('post/user_data', message))

    # Uncomment the following lines to test the ADS GET requests
    # print(interface.get('get/user_data'))
    # print(interface.get('get/spreads'))
    # print(interface.get('get/config?config_file=LOG')) # set config_file to LOG, DATASERVER, or OMS
    ########## ADS INTERFACE ##########


    # Message to be sent to LOG as a payload
    # import datetime
    # log = {
    #         "Section": "Test",
    #         "Severity": "INFO",
    #         "Message": "This is a test log via API",
    #         "Send time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    #         "Publish": 1,
    #         "Tage" : ""
    #     }
    
    # URL of the LOG server
    # DEV
    # url = 'http://localhost:8081/'
    # PROD
    # url = 'http://15.207.12.225:9092/'
    
    ########## LOG INTERFACE ##########

    
    # Initialize the LOG interface
    # interface = LOG_Interface(url)

    # Uncomment the following lines to test the LOG POST requests
    # print(interface.post('post/log', str(log)))
    
    # Uncomment the following lines to test the LOG GET requests
    # print(interface.get('get/log?condition=All'))
    # print(interface.get('get/log?condition=Publish&value=0')) # set condition to Publish, Severity, Date or Section and value for the condition
    ########## LOG INTERFACE ##########
    pass
    