import requests
import json
import traceback


class OPENAPI:
    def __init__(self, username, password, groupid, prodcode, log_interface):
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
                self.log_interface.postLog(severity='INFO',message='OMSB: ODIN login (preprocess) for {}.'.format(self.username),publish=0)
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
            
            print(response.text)
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
            self.log_interface.postLog(severity='INFO',message='OMSB: ODIN login for {}.'.format(self.username),publish=0)
            # return self.authenticate_user(self.jsessionIdencrypted)
        except Exception as e:
            print(e)
            traceback.print_exc()

    def place_order(self, position, scriptkn, instrument, symbol, expirydate, buysell, org_qty,ord_price=0):
        """ 
        If position is BUY, buysell == 1
        """
        self.ClientOrdNum = self.ClientOrdNum + 1

        try:

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
                        "ExpDt": expirydate,
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
                        "RecoId": ""
                    },
                    "ProdCode": self.prodcode,
                    "TaskName": "SendOrderRequest"
                }
            }


            headers = {
                'Accept': '*/*',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            response = requests.request("POST", url, headers=headers, json=payload)
            
            if response.json()['ResponseStatus'] == True:
                print("Order placed!")

                # Save the response object as a log (whole dict)

                print()
                return response.json()
            else:   
                print("Order failed!")
                return False
        except Exception as e:
            print(e)
            traceback.print_exc()

            return []


## Main ##
# if __name__ == "__main__":
#     openAPI = OPENAPI('ACM1019', 'abcd12345', 'HO', '12')

#     # Login
#     openAPI.login() # Login is called in the constructor

#     # Place Order SAMPLE
#     # print(openAPI.place_order("BUY", "62809", "FUTIDX", "NIFTY", "29DEC2022", "1", "50", "1868000"))
