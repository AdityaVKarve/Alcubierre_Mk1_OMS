
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

class Main:
    def __init__(self) -> None:
        self.DEBUG = False
        if len(sys.argv) > 1 and sys.argv[1] == 'debug':
            print('DEBUG mode enabled.')
            self.DEBUG = True

        self.LOGIN_TIME = datetime.strptime("09:00:00",'%H:%M:%S').time()
        self.SLEEP_TIME = datetime.strptime("15:35:00",'%H:%M:%S').time()
        self.start()
        

    def start(self):
        while True:
            now = datetime.now()
            if now.time() > self.LOGIN_TIME and now.time() < self.SLEEP_TIME and isTradingDay(now):
                try:
                    self.ads_interface = ADS_Interface()
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
            self.log_interface.postLog(severity="CRITICAL",message="Failed to get user data.",publish=1)
        
        try:
            spread_list = self.ads_interface.get_spreads()
            self.ads_interface.update_config()
            self.log_interface.postLog(severity='INFO',message='Spreads obtained.', publish=0)
        except Exception as e:
            self.log_interface.postLog(severity="CRITICAL",message="Failed to get spreads.",publish=1)
        
        try:
            config = Config()
            config.refresh_config()
            self.log_interface.postLog(severity='INFO',message='Config file obtained.', publish=0)
        except Exception as e:
            self.log_interface.postLog(severity="CRITICAL",message="Failed to get config file.",publish=1)

        try:
            #=================================
            # Starting the LTP gather thread #
            #=================================
            kite_ticker = auto_login_zerodha_ticker(config=config,log_interface=self.log_interface, debug=self.DEBUG)
            g = GatherLTP(kws = kite_ticker, log_interface = self.log_interface)
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
