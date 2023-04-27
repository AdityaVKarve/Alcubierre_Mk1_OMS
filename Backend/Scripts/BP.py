import datetime
import requests
import json
import traceback
from Log_Server_Interface import Log_Server_Interface

class BPWEALTH:
    def __init__(self, username, password, groupid, prodcode, log_interface: Log_Server_Interface):
        self.username = username
        self.password = password
        self.groupid = groupid
        self.prodcode = prodcode
        self.url_encryption = "https://wave.bpwealth.com:30002/scripsearch/generateEncryptedPassword?pwd="
        self.log_interface = log_interface
        self.jsessionIdencrypted = None
        self.password_encrypted = None

        self.ClientOrdNum = 0

        # Login
        self.login()

    def encryption(self, msg):
        """ 
        To encrypt the password/JSession ID

        """
        try:
            url = self.url_encryption + msg
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            response = requests.request("GET", url, headers=headers)

            print("Encryption completed!")
            return response.text
        
        except Exception as e:
            print(e)
            traceback.print_exc()
            

    def login_(self, pswd):
        self.log_interface.postLog(severity='INFO',message='BPWealth login for {}.'.format(self.username),publish=0,tag='')
        """ 
        To login to the API

        """

        try:
            url = "https://wave.bpwealth.com:30002/get/executeTask"
            payload = {
                "parameters": {
                    "jSessionID": "",
                    "jKey": "",
                    "jData": {
                        "MsgCode": "261",
                        "UserID": self.username,
                        "GroupID": self.groupid,
                        "Pwd": pswd,
                        "NewPwd": "WGpiC8unPDGvRvBsltcTFRJuppoRWmAZski+03N2B8CeY75zuCOcVBFUqhrRdeGBb/omOf/BfmvoZsLeaKpExdo5V5QnGp8Stw2JYrd2RsLQaG+xjxON/7IkHV1vjST8cGlmkNPWVpXoyGJjJtDcV4ZZasDFMJLnTCtH39lHJb0=",
                        "ConnectionType": 4,
                        "PwdEncrypt": True,
                        "IPAddr": "",
                        "LoginTag": self.prodcode,
                        "ForceLoginTag": 1,
                        "AuthenticateFlag": 0,
                        "SSOToken": "",
                        "IFrame": False
                    },
                    "ProdCode": self.prodcode,
                    "TaskName": "Login"
                }
            }
            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            response = requests.request("POST", url, headers=headers, json=payload)

            # print(response.text)
            if response.json()['ResponseStatus'] == False:
                print("Login failed!")
                return False
            else:
                self.ClientOrdNum = int(response.json()['ResponseObject']['ClientOrdNo'])
                # print("ClientOrdNum: ", self.ClientOrdNum)
                print("Login completed!")
                # self.log_interface.postLog(severity='INFO',message='OMSB: ODIN login (preprocess) for {}.'.format(self.username),publish=0)
                # Return jSession ID
                
                return response.json()['ResponseObject']['SessionId']
        except Exception as e:
            print(e)
            traceback.print_exc()

    def authenticate_user(self, jsessionid_encrypted):
        """
        To authenticate the user

        """
        try:
            url = "https://wave.bpwealth.com:30002/get/executeTask"

            payload = {
                "parameters": {
                    "jSessionID": jsessionid_encrypted,
                    "jKey": "",
                    "jData": {
                        "UserID": self.username,
                        "GroupID": self.groupid,
                        "UCCClientID": "",
                        "UCCGroupID": "",
                        "Token": "9824403426",
                        "IsLoginAuth": True,
                        "SSOLoginSession": False,
                        "TwoFAType": "TOTP"
                    },
                    "ProdCode": self.prodcode,
                    "TaskName": "AuthenticateUser"

                }
            }


            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            response = requests.request("POST", url, headers=headers, json=payload)
            

            # Check what is response type
            print(type(response))
            if response.json()['ResponseStatus'] == True:
                print("Authentication completed!")
                print("JSession ID: ", jsessionid_encrypted)
                print(response.json())
                return True
            else:
                print("Authentication failed!")
                return False

        except Exception as e:
            print(e)
            traceback.print_exc()


    def login(self):
        """ 
        Login : To login to the API and set the JSession ID

        Flow : encryption password -> login_ -> get jsessionId -> encrypt jsessionId -> authenticate_user
        """

        try:
            self.password_encrypted = self.encryption(self.password)
            jsessionid = self.login_(self.password_encrypted)

            self.jsessionIdencrypted = self.encryption(jsessionid)
            print("JSession ID: ", self.jsessionIdencrypted)
            # self.log_interface.postLog(severity='INFO',message='OMSB: ODIN login for {}.'.format(self.username),publish=0)
            # return self.authenticate_user(self.jsessionIdencrypted)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def get_orderbook(self):
        try:

            url = "https://wave.bpwealth.com:30002/get/executeTask"

            payload = {
                "parameters": {
                    "jSessionID": self.jsessionIdencrypted,
                    "jKey": "",
                    "jData": {
                        "UserID": self.username,
                        "GroupID": self.groupid,
                        "UCCClientID": "",
                        "UCCGroupID": "",
                        "MktSegId": 0,
                        "ProductType": "",
                        "Status": ""
                    },
                    "ProdCode": self.prodcode,
                    "TaskName": "GetOrderBook"
                }
            }


            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            response = requests.request("POST", url, headers=headers, json=payload)
            
            if response.json()['ResponseStatus'] == True:
                print("Order book fetched!")
                print(response.json())

                # Save the response object as a log (whole dict)

                return response.json()
            else:   
                print("Order failed!")
                return False
        except Exception as e:
            print(e)
            traceback.print_exc()

            return []

    def get_order_details(self, order_id):
        """ Ordeer_id is reco_id from place_order function """

        try:
            orderbook = self.get_orderbook()
            for order in orderbook["ResponseObject"]["objJSONRows"]:
                if order["RecoId"] == order_id:
                    return order
        except Exception as e:
            print(e)
            traceback.print_exc()

    
    def place_order(self, position, scriptkn, instrument, symbol, buysell, org_qty,ord_price=0):
        """ 
        If position is BUY, buysell == 1
        """
        self.login()
        self.ClientOrdNum = self.ClientOrdNum + 1

        try:
            # hash value of current time : limited to 10 charecters : as order_tag
            hash_value = hash(str(datetime.datetime.now())) 
            order_tag = str(hash_value)[:10]

            print("Order tag: ", order_tag)

            url = "https://wave.bpwealth.com:30002/get/executeTask"

            payload = {
                "parameters": {
                    "jSessionID": self.jsessionIdencrypted,
                    "jKey": "",
                    "jData": {
                        "MsgCode": 121,
                        "UserID": self.username,
                        "GroupID": self.groupid,
                        "IsSpread": False,
                        "ModifyFlag": False,
                        "CancelFlag": False,
                        "IsSpreadScrip": 0,
                        "OrderSide": position,
                        "MKtSegId": "2",
                        "ScripTkn": scriptkn,
                        "OrdType": "2",
                        "BuyOrSell": buysell,
                        "OrgQty": org_qty,
                        "DiscQty": 50,
                        "OrdPrice": ord_price,
                        "TrigPrice": "0",
                        "Validity": "1",
                        "Days": "0",
                        "Instrument": instrument,
                        "OrdGTD": "0",
                        "ExchOrdNo": "0",
                        "ProdType": "D",
                        "InstrumentId": "",
                        "Symbol": symbol,
                        "Series": "",
                        "ExpDt": "",
                        "StrkPrc": "0",
                        "OptType": "",
                        "MktLot": "50",
                        "PrcTick": "5",
                        "OrdTime": "0",
                        "ParticipantId": "",
                        "ClientOrdNo": self.ClientOrdNum,
                        "GatewayOrdNo": "0",
                        "MPExpVal": "",
                        "MPStrkPrcVal": "",
                        "MPBasePrice": "",
                        "MPMFFlag": "",
                        "MPFirstLegPrice": 0,
                        "BOSLOrderType": "",
                        "SLTriggerPrice": 0,
                        "ProfitOrderPrice": 0,
                        "SLJumpPrice": 0,
                        "LTPJumpPrice": 0,
                        "BracketOrderId": "",
                        "LegIndicator": 0,
                        "BOModifyTerms": "",
                        "SPOSType": "0",
                        "FIILimit ": "0",
                        "NRILimit": "0",
                        "IsSOR": False,
                        "MktProt": 0,
                        "Col": 1,
                        "OFSMargin": "",
                        "RecoId": order_tag,
                    },
                    "ProdCode": self.prodcode,
                    "TaskName": "SendOrderRequest"
                }
            }
            # print(payload)

            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            response = requests.request("POST", url, headers=headers, json=payload)
            # print(response.json())
            
            if response.json()['ResponseStatus'] == True:
                print("Order placed!")

                # Save the response object as a log (whole dict)
                return response.json(), order_tag
            else:   
                print("Order failed!")
                return False
        except Exception as e:
            print(e)
            traceback.print_exc()

            return []


# Main ##
# if __name__ == "__main__":
#     openAPI = BPWEALTH('AC217', 'abcd2222', 'HO', '12')
#     # 2FA 9408644613

#     # Login
#     openAPI.login() # Login is called in the constructor

#     # Get Order Book
#     # orderbook = openAPI.get_orderbook()

#     # Place Order SAMPLE
#     # print(openAPI.place_order(position="BUY", scriptkn="47223", instrument="OPTIDX", symbol="NIFTY",buysell="1", org_qty="50", ord_price="535"))
#     # {'ResponseStatus': True, 'ResponseObject': '64=121|5022=Order Submitted', 'ResponseCode': 0, 'ErrorMessages': None}

#     # Create a json file and dump the response object

#     # with open('response.json', 'w') as f:
#     #     json.dump(orderbook, f, indent=4)

#     # Get Order Details
#     # order_details = openAPI.get_order_details(order_id="6379643263")
#     order_details = openAPI.get_order_details(order_id="-690855549")
#     print(order_details)
