import datetime
import json
import re
import requests
from Config import Config
from Log_Server_Interface import Log_Server_Interface
def pretty_print(json_data):
    print(json.dumps(json_data, indent=4, sort_keys=True))


class ODIN:
    def __init__(self, login_details, log_interface: Log_Server_Interface) -> None:
        self.log_interface = log_interface
        self.log_interface.postLog(severity='INFO',message='ODIN login for {}.'.format(login_details['CLIENT_CODE']),publish=0)
        self.client_code = login_details["CLIENT_CODE"]
        self.client_passward = login_details["CLIENT_PASSWORD"]
        self.client_2fa = login_details["CLIENT_2FA"]
        self.client_api_key = login_details["CLIENT_API_KEY"]
        self.url = (
            "https://jri4df7kaa.execute-api.ap-south-1.amazonaws.com/prod/interactive"
        )
        self.header = {}

        # LOGIN
        self.login()

    def login(self):
        print("Logging in")
        data = json.dumps({
            "user_id": self.client_code,
            "login_type": "PASSWORD",
            "password": self.client_passward,
            "second_auth": self.client_2fa,
            "api_key": self.client_api_key,
            "source": "MOBILEAPI"
        })

        # print(data)

        header = {
            "Content-Type": "application/json",
        }

        try:
            # print("TEST")
            r = requests.post(
                self.url + "/authentication/v1/user/session", headers=header, data=data
            ).json()
            print("TEST")
            # print(r)
            access_token = r["data"]["access_token"]
            self.header = {"Authorization": "Bearer {}".format(access_token)}

            self.log_interface.postLog(severity='INFO',message='ODIN login succesful for {}.'.format(self.client_code),publish=0)


        except Exception as e:
            print("ER: ", e)
            print("Login Failed")

    def place_order(self, scrip_token, symbol, quantity, order_type, expiry_date=None):
        print("Placing Order")
        data = {
            "scrip_info": {
                "exchange": "NSE_FO",
                "scrip_token": int(scrip_token),
                "symbol": symbol,
                "series": None,
                "expiry_date": None,
                "strike_price": None,
                "option_type": None,
            },
            "transaction_type": order_type,
            "product_type": "DELIVERY",
            "order_type": "RL-MKT",
            "quantity": abs(int(quantity)),
            "price": None,
            "trigger_price": None,
            "disclosed_quantity": None,
            "validity": "IOC",
        }

        r = requests.post(
            self.url + "/transactional/v1/orders/regular",
            headers=self.header,
            json=data,
        ).json()
        print("TEST 2")
        print(r)
        return r

    def order_history(self, order_id):
        print("Order History")
        r = requests.get(
            self.url + "/transactional/v1/orders/{}".format(order_id),
            headers=self.header,
        ).json()
        print("TEST 3")
        return r

if __name__ == "__main__":
    LOGIN_DETAILS = {
        "CLIENT_CODE": "NB01",
        "CLIENT_PASSWORD": "odin@123",
        "CLIENT_2FA": "9460454571",
        "CLIENT_API_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzUGFydG5lckFwcElkIjoiMDFGMDBGIiwiQjJDIjoiWSIsIlB1Ymxpc2hlck5hbWUiOiJJbmRpcmEgU2VjdXJpdGllcyBQdnQgTHRkIC0gQjJDIiwic1B1Ymxpc2hlckNvZGUiOiJjdSIsIkN1c3RvbWVySWQiOiIzODUiLCJzQXBwbGljYXRpb25Ub2tlbiI6IkluZGlyYVNlY3VyaXRpZXNCMkMxMDcwNDY0ZGVlZiIsInVzZXJJZCI6Ik5CMDEiLCJCcm9rZXJOYW1lIjoiSW5kaXJhIFNlY3VyaXRpZXMgUHZ0IEx0ZCIsImV4cCI6OTExNzczMzIwMCwiaWF0IjoxNjUyNzczMjU4fQ.UpOSoLuaZw7u5bTx714jXLPDn6mrl39BKCLtWBg3bI8"
    }

    odin = ODIN(LOGIN_DETAILS, Log_Server_Interface(Config()))
    #order_details = odin.place_order(scrip_token=58448, symbol="NIFTY", quantity=50, order_type="SELL")['data']
    print(odin.order_history('NYIYI0001183'))
    # order_details = odin.place_order(scrip_token=58446, symbol="NIFTY", quantity=50, order_type="BUY")['data']
    # order_id = order_details['orderId']
    # order_details = odin.order_history(order_id="NYIYI00001D2")['data']
    # for order in order_details:
    #     # print(order, " ", order['order_price'])
    #     if order['status'] == 'EXECUTED':
    #         print(order['order_price'])
    # odin.order_history(order_id="NYIYI00002D2")
    # odin.order_history(order_id="NYIYI00001D2")
    # tradingsymbol = 'NIFTY23FEBFUT'
    # tradingsymbol = 'BANKNIFTY23FEBFUT'
    # CHECK
    # If nomenclature -> if has NIFTY, then use NIFTY, else use BANKNIFTY (using re as trading symbol is string, eg : NIFTY23FEBFUT)
    # if re.search('BANKNIFTY',tradingsymbol):
    #     symbol = 'BANKNIFTY'
    # else:
    #     symbol = 'NIFTY'
    # print(symbol)




# 'message' = {'status': 'success', 'code': 's-101', 'message': 'Order Entry Sent to OMS', 'data': {'orderId': 'NYIYI00001D2'}} # BUY
# 'message' = {'status': 'success', 'code': 's-101', 'message': 'Order Entry Sent to OMS', 'data': {'orderId': 'NYIYI00002D2'}} # SELL
