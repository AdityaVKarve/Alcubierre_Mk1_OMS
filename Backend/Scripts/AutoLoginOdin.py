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

        header = {
            "Content-Type": "application/json",
        }

        try:
            r = requests.post(
                self.url + "/authentication/v1/user/session", headers=header, data=data
            ).json()
            access_token = r["data"]["access_token"]
            self.header = {"Authorization": "Bearer {}".format(access_token)}
            self.log_interface.postLog(severity='INFO',message='ODIN login succesful for {}.'.format(self.client_code),publish=0)


        except Exception as e:
            self.log_interface.postLog(severity='CRITICAL',message='ODIN login failed for {}. Error: {}.'.format(self.client_code,e),publish=1)

    def place_order(self, scrip_token, symbol, quantity, order_type, expiry_date=None):
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
        self.log_interface.postLog(severity='INFO',message='ODIN order placed for {}, instrument: {}, type: {}.'.format(self.client_code,scrip_token, type),publish=1)
        return r

    def order_history(self, order_id):
        r = requests.get(
            self.url + "/transactional/v1/orders/{}".format(order_id),
            headers=self.header,
        ).json()
        return r

