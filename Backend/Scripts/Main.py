
import cProfile
import json
import time
from ADS_Interface import ADS_Interface
from Config import Config
from Log_Server_Interface import Log_Server_Interface
from datetime import datetime
from ValidDayChecker import isTradingDay
from UserProfileGenerator import UserProfileGenerator
import DBManager
from random import randint
from time import sleep
from OrderHandler import OrderHandler
from GatherLTP import GatherLTP
from AutoLoginKiteTicker import auto_login_zerodha_ticker
from Log_Server_Interface import Log_Server_Interface 
import sys
import Logs
import requests

class Main:
    def __init__(self) -> None:
        self.DEBUG = False
        self.SLIPPAGE = True
        if len(sys.argv) > 1 and sys.argv[1] == 'debug':
            print('DEBUG mode enabled.')
            self.DEBUG = True
            self.LOGIN_TIME = datetime.strptime("00:00:00",'%H:%M:%S').time()
            self.SLEEP_TIME = datetime.strptime("23:59:00",'%H:%M:%S').time()
        else:
            self.LOGIN_TIME = datetime.strptime("09:00:00",'%H:%M:%S').time()
            self.SLEEP_TIME = datetime.strptime("15:35:00",'%H:%M:%S').time()

        self.start()

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

    def slippage_report(self):
        # self.log_interface = Log_Server_Interface(config=self.config)
        # self.config = Config()
        # self.config.refresh_config()
        # This function is called at the end of the day to generate a slippage report by hitting an API
        # The API will be called only if the day is a trading day

        # Get the slippage report from the DB : orerHistory table
        conn = DBManager.get_new_dbconnection()
        cur = conn.cursor()

        # Get the slippage report from the DB : orderHistory table where order_time is today
        today = datetime.now().date()
        query = f"SELECT order_time,instrument_nomenclature, tradingsymbol, order_price, position  FROM order_history WHERE DATE(order_time) = '{today}'" 
        print(query)
        cur.execute(query)
        slippage_report = cur.fetchall()

        print(len(slippage_report))
        return
        data = []

        for row in slippage_report:
            data.append({
                'end_date': row[0],
                'instrument_nomenclature': row[1],
                'trading_symbol': row[2],
                'price': row[3],
                'position': row[4]
            })

        # hit the API with the slippage report
        # API call
        headers = {
            'Authorization': 'Bearer ' + ""
        }
        url = 'http://13.233.26.147:9000/candlestick/'
        try:
            response = requests.get(url, headers=headers, json=data)
            sleep(10)
            if response.status_code == 200:
                print('Slippage report sent successfully')
                # self.log_interface.postLog(severity="INFO",message='Sent Slippage report',publish = 1)
                return True
            else:
                print('Slippage report not sent')
                # self.log_interface.postLog(severity="CRITICAL",message='Failed to sent Slippage report',publish = 1)
                return False
        except Exception as e:
            print(e)
            # self.log_interface.postLog(severity="CRITICAL",message=f'Failed to sent Slippage report: {e}',publish = 1)
            return False

    def start(self):
        while True:
            now = datetime.now()
            if now.time() > self.LOGIN_TIME and now.time() < self.SLEEP_TIME and isTradingDay(now):
                try:
                    self.SLIPPAGE = True
                    self.ads_interface = ADS_Interface()
                    if self.DEBUG == False:
                        self.ads_interface.update_config()
                    self.config = Config()
                    self.config.refresh_config()
                    self.log_interface = Log_Server_Interface(config=self.config)
                    self.log_interface.postLog(severity='INFO',message='Finvant Alcubierre Mk1 OMS Backend turned on.', publish=1)
                    
                except Exception as e:
                    print(e)
                    Logs.logCritical(severity="CRITICAL",message='Failed to initialise Log server/ADS.',publish = 1, tag = 'OMSB_MAIN_1')
                self.main_loop()
            else:
                if now.time() > self.SLEEP_TIME and self.SLIPPAGE == True:
                    # Logs.logInfo(severity='INFO',message='OMS Backend sleeping.', publish=0)
                    ## EOD : Slippage code 
                    self.slippage_report()
                    self.SLIPPAGE = False
                    pass
                sleep(100)
    
    def main_loop(self):

        #The main loop runs from login to 15:30, and spawns all the needed child threads
        self.log_interface.postLog(severity='INFO',message='OMS Backend mainloop started.', publish=0)

        #============================================
        # Getting ADS data (user data, spreads etc) #
        #============================================
        try:
            user_data = self.ads_interface.get_user_data()
            self.log_interface.postLog(severity='INFO',message='User data obtained.', publish=0)
        except Exception as e:
            self.log_interface.postLog(severity="CRITICAL",message="Failed to get user data.",publish=1, tag = 'OMSB_MAIN_6')
        
        try:
            spread_list = self.ads_interface.get_spreads()
            if self.DEBUG == False:
                self.ads_interface.update_config()
            self.log_interface.postLog(severity='INFO',message='Spreads obtained.', publish=0)
        except Exception as e:
            self.log_interface.postLog(severity="CRITICAL",message="Failed to get spreads.",publish=1, tag = 'OMSB_MAIN_7')
        
        try:
            config = Config()
            config.refresh_config()
            self.log_interface.postLog(severity='INFO',message='Config file obtained.', publish=0)
        except Exception as e:
            self.log_interface.postLog(severity="CRITICAL",message="Failed to get config file.",publish=1, tag = 'OMSB_MAIN_8')

        try:
            #=================================
            # Starting the LTP gather thread #
            #=================================
            kite_ticker = auto_login_zerodha_ticker(config=config,log_interface=self.log_interface, debug=self.DEBUG)
            g = GatherLTP(kws = kite_ticker, log_interface = self.log_interface, config = self.config)
            g.start_LTP_thread()
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to start LTP thread.',publish = 1, tag = 'OMSB_MAIN_3')

        try:
            #===========================
            # Generating user profiles #
            #===========================
            user_dict = UserProfileGenerator().create_user_profiles(user_data=user_data, log_interface=self.log_interface, debug=self.DEBUG)
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to generate user dictionary.',publish = 1, tag = 'OMSB_MAIN_4')
        
        try:
            #====================================
            # Starting the order handler thread #
            #====================================
            order_handler = OrderHandler(user_profiles=user_dict, spread_list=spread_list, log_interface = self.log_interface, debug=self.DEBUG)
            order_handler.start_order_handler()
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failure in order handler.',publish = 1, tag = 'OMSB_MAIN_5')

        while datetime.now().time() < self.SLEEP_TIME:
            sleep(10)

if __name__ == '__main__':
    # cProfile.run('main()', filename='worker.prof')
    m = Main()
