import json
import sys
import time
import DBManager
from datetime import datetime, timedelta
from random import randint
import threading
from time import sleep
from OrderPlacement import placeOrder
from Log_Server_Interface import Log_Server_Interface

class OrderHandler:
    def __init__(self, user_profiles: dict, spread_list: dict, log_interface: Log_Server_Interface, debug:bool = False) -> None:
        self.user_profiles = user_profiles
        self.log_interface = log_interface
        self.SLEEP_TIME = datetime.strptime("23:59:00",'%H:%M:%S').time()
        self.spread_list = spread_list
        self.DEBUG = debug

        self.place_times = []
        self.kill = []

        self.conn = ''  # RECORD : time taken for individual orders to be placed -> Placing to placed (in orderbook) | to avoid api rate limit | class variable time_taken (list) -> saves time taken for each order to be placed
        

    
    def start_order_handler(self):
        try:
            if self.DEBUG:
                print('Creating order handler sub threads.')
            user_threads = []
            for ctr,u in enumerate(self.user_profiles):
                self.kill.append(False)
                user_threads.append(self.create_user_thread(u, ctr))
            
            if self.DEBUG:
                print('Starting order handler sub threads.')
            for u in user_threads:
                u.start()
        except:
            self.log_interface.postLog(severity="CRITICAL",message='Failed to start order handler sub threads.',publish = 1, tag = 'OMSB_OH_1')


    def create_user_thread(self,username, thread_no):
        thread = threading.Thread(target = self.thread_function, args=[username, thread_no])
        thread.setDaemon(True)
        return thread

    def thread_function(self, username, thread_no):
        
        while datetime.now().time() < self.SLEEP_TIME:
            try:
                self.place_pending_orders(username, spread_list= self.spread_list, cntr = thread_no)
            except:
                self.log_interface.postLog(severity="CRITICAL",message='Failed to clear pending orders.',publish = 1, tag = 'OMSB_OH_2')
            sleep(0.001)

    

    def place_pending_orders(self,username: str, spread_list: dict, cntr):
        if self.DEBUG:
            print('Placing pending orders for user : ', username)

        user_type = self.user_profiles[username]['USER_TYPE']
        brokerage_object = self.user_profiles[username]['BROKERAGE_OBJECT']
        paper_trade = self.user_profiles[username]['PAPER_TRADE']
        pending_orders = DBManager.get_pending_orders(username)
        for p in pending_orders:
            if self.DEBUG:
                print('PENDING ORDERS: ', pending_orders)
            tradingsymbol = p['tradingsymbol']
            exchange_token = p['exchange_token']

            lot_size = p['lot_size']
            total_qty = p['total_qty']
            placed_qty = p['placed_qty']
            instrument_token = int(p['instrument_token'])
            qty_to_place = min(abs(total_qty - placed_qty),1)
            qty_to_place*=(total_qty - placed_qty)/abs(total_qty - placed_qty)
            qty_to_place = int(qty_to_place)
            last_placement = p['last_placement']
            exchange = p['exchange']
            segment = p['segment']
            
            if last_placement == '0' or datetime.now() > datetime.strptime(last_placement,'%Y-%m-%d %H:%M:%S') + timedelta(seconds=7):
                if self.kill[cntr]:
                    return
                k = placeOrder(user_type=user_type,username=username,tradingsymbol=tradingsymbol,exchange_token=exchange_token,instrument_token=instrument_token,lot_size=lot_size,qty=qty_to_place,exchange=exchange, segment= segment,brokerage_object=brokerage_object,spread_list=spread_list,log_interface=self.log_interface, paper_trade=paper_trade, debug=self.DEBUG)
                if k == True:
                    self.kill[cntr] = True
                # Add a 5s delay to avoid order placement failure
                sleep(0.28)
                
    
        