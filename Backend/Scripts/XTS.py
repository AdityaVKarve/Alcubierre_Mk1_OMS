from datetime import datetime
from Log_Server_Interface import Log_Server_Interface
import json
import requests

class XTS:
    def __init__(self, token:str, client_id:str, endpoint:str, log_interface:Log_Server_Interface) -> None:
        self.header = {'Content-Type': 'application/json', 'Authorization': token}
        self.client_id = client_id
        self.endpoint = endpoint
        self.log_server_interface = log_interface
    
    def place_order(self,exchange_token:int, order_type:str, position:str, quantity:int, limit_price:float = 0):
        print("LIMIT PRICE:{}".format(limit_price))
        self.log_server_interface.postLog('INFO','attempting XTS order. Token:{}, Position:{}, Quantity:{}.'.format(exchange_token,position,quantity),0)
        parameters = {
            "exchangeSegment": "NSEFO",
            "exchangeInstrumentID": exchange_token,
            "productType": "NRML",
            "orderType": order_type,
            "orderSide": position,
            "timeInForce": "DAY",
            "disclosedQuantity": 0,
            "orderQuantity": quantity,
            "limitPrice": limit_price,
            "stopPrice": 0,
            "orderUniqueIdentifier": datetime.now().strftime('%H%M%S_{}'.format(position))
        }
        parameters['clientID'] = self.client_id
        parameters = json.dumps(parameters)
        print(parameters)
        r = requests.post(self.endpoint+"/interactive/orders", data=parameters, headers=self.header).json()
        print(r)
        self.log_server_interface.postLog('INFO','XTS order placed. Token:{}, Position:{}, Quantity:{}.'.format(exchange_token,position,quantity),0)
        return r['result']['AppOrderID']

    def order_history(self,order_id:int):
        params = {'appOrderID': order_id}
        params['clientID'] = self.client_id
        r = requests.get(url = self.endpoint+"/interactive/orders", params=params, headers=self.header)
        return r.json()