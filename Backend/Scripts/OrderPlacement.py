import re
import sqlite3
import sys
import time
from kiteconnect import KiteConnect
from random import randint
from DBManager import update_order_placement
from Log_Server_Interface import Log_Server_Interface
import json
from time import sleep
from Logs import logInfo

def myround(x, base=5):
    return base * round(x/base)

def placeOrder(user_type, username, tradingsymbol, exchange_token, instrument_token, lot_size, qty , exchange, segment, brokerage_object, spread_list, log_interface: Log_Server_Interface, paper_trade, debug: bool = False):
    time_before = (time.time())
    conn = sqlite3.connect('../../C/Data/OrderData.db')
    cur = conn.cursor()

    if debug:
        print('Placing order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))

    while True:
        try:
            if debug:
                print('Trying to open LTP_Table.json')
            with open('../Data/LTP_table.json') as f:
                LTP_Table = json.load(f)
            break
        except:
            if debug:
                print('Failed to open LTP_Table.json')
            # if json is empty, create an empty dict
            if sys.getsizeof(f) == 3:
                LTP_Table = {}
                with open('../Data/LTP_Table.json', 'w') as f:
                    json.dump(LTP_Table, f)
            sleep(1)
            continue

    if user_type == 'ZERODHA':
        if qty > 0:
            transaction_type = 'BUY'
        else:
            transaction_type = 'SELL'
        
        if segment == 'NFO-OPT':
            #Options
            try:
                ltp = LTP_Table[str(instrument_token)]
            except Exception as e:
                print('Failed to get LTP for instrument token:{}'.format(instrument_token))
                print(e)
                return
            
            try:
                if qty > 0:
                    price = ltp*1.01
                else:
                    price = ltp*0.99
                price = myround(price,0.5)

                if paper_trade == False:
                    if debug:
                        print('Placing live Zerodha order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = brokerage_object.place_order(variety='regular', exchange=exchange, tradingsymbol=tradingsymbol, transaction_type=transaction_type, quantity=abs(qty*lot_size), product=brokerage_object.PRODUCT_NRML, order_type=brokerage_object.ORDER_TYPE_LIMIT, price=price, validity=None, disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None)
                    orders = brokerage_object.order_history(order_id = order_id)
                    time.sleep(1)
                    logInfo('Zerodha order details')
                    logInfo(orders)
                    for order in orders:
                        if order['status'] == 'COMPLETE':
                            placed_price = order['average_price']

                else:
                    if debug:
                        print('Placing PAPER order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = randint(1,1000)
                    placed_price = ltp
                time.sleep(0.5)
                try:
                    log_interface.postLog(severity='INFO',message='Placed Zerodha Kite options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                except:
                    placed_price = ltp
                    log_interface.postLog(severity='INFO',message='Placed Zerodha Kite options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                

            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place Zerodha Kite options order. User: {}. Tradingsymbol:{}. QTY:{} .'.format(username,tradingsymbol,qty*lot_size),publish = 1, tag = 'OMSB_OP_1')
                
                order_id = -1 # To avoid recurring orders
                placed_price = LTP_Table[str(instrument_token)]
        else:
            #Futures
            try:
                if paper_trade == False:
                    if debug:
                        print('Placing LIVE order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = brokerage_object.place_order(variety='regular', exchange=exchange, tradingsymbol=tradingsymbol, transaction_type=transaction_type, quantity= abs(qty*lot_size), product=brokerage_object.PRODUCT_NRML, order_type=brokerage_object.ORDER_TYPE_MARKET, price=None, validity=None, disclosed_quantity=None, trigger_price=None, squareoff=None, stoploss=None, trailing_stoploss=None, tag=None)
                    orders = brokerage_object.order_history(order_id = order_id) 
                    logInfo("Zerodha ORDER DETAIL")
                    logInfo(orders)
                    for order in orders:
                        if order['status'] == 'COMPLETE':
                            placed_price = order['average_price']
                else:
                    if debug:
                        print('Placing PAPER order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = randint(1,1000)
                    placed_price = LTP_Table[str(instrument_token)]
                
                log_interface.postLog(severity='INFO',message='Placed Zerodha Kite futures order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                
            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place Zerodha Kite futures order. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_2')
                order_id = -1
                placed_price = LTP_Table[str(instrument_token)]

        try:
            update_order_placement(username=username,tradingsymbol=tradingsymbol,placed_qty=qty,placed_price=placed_price, spread_list=spread_list, brokerage_name=user_type, brokerage_id=order_id, debug=debug) # If this fails, infinite order placement -> stop this thread + critical user message
        except:
            # kill the thread to avoid infinite order placement
            log_interface.postLog(severity="CRITICAL",message='Failed to update order placement in DB. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_3')
            return True
        
        # commit changes
        conn.commit()
            
        time_after = (time.time())      
        placed_time = (time_after-time_before)*1000
        
        log_interface.postLog(severity="INFO",message=str(placed_time),publish = 0, tag = '')

    elif user_type == 'XTS':
        if qty > 0:
            transaction_type = 'BUY'
        else:
            transaction_type = 'SELL'
        
        if segment == 'NFO-OPT':
            #Options
            try:
                ltp = LTP_Table[str(instrument_token)]
            except Exception as e:
                print('Failed to get LTP for instrument token:{}'.format(instrument_token))
                print(e)
                return
            
            try:
                if qty > 0:
                    price = ltp*1.01
                else:
                    price = ltp*0.99
                price = myround(price,0.5)
                if paper_trade == False:
                    if debug:
                        print('Placing live XTS order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = brokerage_object.place_order(exchange_token = int(exchange_token), order_type = 'LIMIT', position = transaction_type, quantity = abs(qty*lot_size), limit_price = price)
                    time.sleep(1)
                    orders = brokerage_object.order_history(order_id = order_id)
                    logInfo("XTS ORDER DETAIL")
                    logInfo(orders)
                    for order in orders['result']:
                        if order['OrderAverageTradedPrice'] != "":
                            placed_price = float(order['OrderAverageTradedPrice'])
                else:
                    if debug:
                        print('Placing PAPER order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = randint(1,1000)
                    placed_price = ltp
                try:
                    log_interface.postLog(severity='INFO',message='Placed XTS options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1, tag='ORDER')
                except:
                    placed_price = ltp
                    log_interface.postLog(severity='INFO',message='Placed XTS options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1, tag='ORDER')
                

            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place XTS options order. User: {}. Tradingsymbol:{}. QTY:{} .'.format(username,tradingsymbol,qty*lot_size),publish = 1, tag = 'OMSB_OP_1')
                
                order_id = -1 # To avoid recurring orders
                placed_price = LTP_Table[str(instrument_token)]
        else:
            #Futures
            try:
                if paper_trade == False:
                    if debug:
                        print('Placing XTS order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = brokerage_object.place_order(exchange_token = int(exchange_token), order_type = 'MARKET', position = transaction_type, quantity = abs(qty*lot_size), limit_price = 0)
                    orders = brokerage_object.order_history(order_id = order_id)
                    logInfo("XTS ORDER DETAIL")
                    logInfo(orders)
                    for order in orders['result']:
                        if order['OrderAverageTradedPrice'] != "":
                            placed_price = float(order['OrderAverageTradedPrice'])
                else:
                    if debug:
                        print('Placing PAPER order for user: {} for tradingsymbol: {} and qty: {}'.format(username, tradingsymbol, qty))
                    order_id = randint(1,1000)
                    placed_price = LTP_Table[str(instrument_token)]
                
                log_interface.postLog(severity='INFO',message='Placed XTS futures order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                
            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place XTS futures order. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_2')
                order_id = -1
                placed_price = LTP_Table[str(instrument_token)]

        try:
            #print("Updating order_placement username:{} tradingsymbol:{} placed_qty:{} placed_price:{} spread_list:{}".format(username,tradingsymbol, qty, placed_price, spread_list))
            update_order_placement(username=username,tradingsymbol=tradingsymbol,placed_qty=qty,placed_price=placed_price, spread_list=spread_list, brokerage_name=user_type, brokerage_id=order_id, debug=debug) # If this fails, infinite order placement -> stop this thread + critical user message
        except:
            # kill the thread to avoid infinite order placement
            log_interface.postLog(severity="CRITICAL",message='Failed to update order placement in DB. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_3')
            return True
        
        # commit changes
        conn.commit()
            
        time_after = (time.time())      
        placed_time = (time_after-time_before)*1000
        
        log_interface.postLog(severity="INFO",message=str(placed_time),publish = 0, tag = '')
    
    # UPDATION REQUIRED USING ODIN (OLD) SCRIPT
    elif user_type == 'ODIN':
        if qty > 0:
            transaction_type = 'BUY'
        else:
            transaction_type = 'SELL'
        
        # CHECK
        # If nomenclature -> if has NIFTY, then use NIFTY, else use BANKNIFTY (using re as trading symbol is string, eg : NIFTY23FEBFUT)
        if re.search('BANKNIFTY',tradingsymbol):
            symbol = 'BANKNIFTY'
        else:
            symbol = 'NIFTY'
        
        if segment == 'NFO-OPT':
            #Options
            try:
                ltp = LTP_Table[str(instrument_token)]
            except Exception as e:
                print(e)
                return
            
            try:
                if qty > 0:
                    price = ltp*1.01
                else:
                    price = ltp*0.99
                price = myround(price,0.5)

                if paper_trade == False:
                    order_detail = brokerage_object.place_order(scrip_token=exchange_token, symbol=symbol, quantity=(qty*lot_size), order_type=transaction_type)
                    time.sleep(1)
                    order_id = order_detail['orderId']
                    orders = brokerage_object.order_history(order_id = order_id)['data']
                    for order in orders:
                        if order['status'] == 'EXECUTED':
                            placed_price = order['order_price']
                else:
                    order_id = randint(1,1000)
                    placed_price = ltp
                try:
                    log_interface.postLog(severity='INFO',message='Placed ODIN options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                except:
                    placed_price = ltp
                    log_interface.postLog(severity='INFO',message='Placed ODIN options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                
            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place ODIN options order. User: {}. Tradingsymbol:{}. QTY:{} .'.format(username,tradingsymbol,qty*lot_size),publish = 1, tag = 'OMSB_OP_1')
                order_id = -1
                placed_price = LTP_Table[str(instrument_token)]
        else:
            #Futures
            try:
                if paper_trade == False:
                    order_detail = brokerage_object.place_order(scrip_token=exchange_token, symbol=symbol, quantity=(qty*lot_size), order_type=transaction_type)['data']
                    order_id = order_detail['orderId']
                    time.sleep(1)
                    orders = brokerage_object.order_history(order_id = order_id)['data']
                    for order in orders:
                        if order['status'] == 'EXECUTED':
                            placed_price = order['order_price']
                    
                else:
                    order_id = randint(1,1000)
                    placed_price = LTP_Table[str(instrument_token)]
                
                log_interface.postLog(severity='INFO',message='Placed ODIN futures order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1,tag='ORDER')
                
            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place ODIN futures order. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_2')
                order_id = -1
                placed_price = LTP_Table[str(instrument_token)]

        try:
            print(placed_price)
            update_order_placement(username=username,tradingsymbol=tradingsymbol,placed_qty=qty,placed_price=placed_price, spread_list=spread_list, brokerage_name=user_type, brokerage_id=order_id, debug=debug) # If this fails, infinite order placement -> stop this thread + critical user message
        except:
            # kill the thread to avoid infinite order placement
            log_interface.postLog(severity="CRITICAL",message='Failed to update order placement in DB. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_3')
            return True
        # commit changes
        conn.commit()
            
        time_after = (time.time())      
        placed_time = (time_after-time_before)*1000
        
        log_interface.postLog(severity="INFO",message=str(placed_time),publish = 0, tag = '')
    
    elif user_type == 'BPWEALTH':
        if qty > 0:
            transaction_type = 'BUY'
        else:
            transaction_type = 'SELL'
        
        # CHECK
        # If nomenclature -> if has NIFTY, then use NIFTY, else use BANKNIFTY (using re as trading symbol is string, eg : NIFTY23FEBFUT)
        if re.search('BANKNIFTY',tradingsymbol):
            symbol = 'BANKNIFTY'
        else:
            symbol = 'NIFTY'
        
        if segment == 'NFO-OPT':
            #Options
            try:
                ltp = LTP_Table[str(instrument_token)]
            except Exception as e:
                print('123 LTP not found for instrument token:{}'.format(instrument_token))
                print(e)
                return
            
            try:
                if qty > 0:
                    price = ltp*1.01
                else:
                    price = ltp*0.99
                price = myround(price,0.5)
                price = price*100
                print('Placing BP WEALTH options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,price))
                if paper_trade == False:
                    if transaction_type == 'BUY':
                        buy_sell = '1'
                    else:
                        buy_sell = '2'
                    # get orde_price from order book using username, tradingsymbol, qty, transaction_type
                    brokerage_object.login()
                    order_details, order_id = brokerage_object.place_order(position=transaction_type, scriptkn=exchange_token, instrument="OPTIDX", symbol=symbol, buysell=buy_sell, org_qty=abs(lot_size*qty), ord_price=int(price))
                    # print(order_details)
                    sleep(1)
                    cntr = 0
                    while cntr < 10:
                        try:
                            placed_price = float(brokerage_object.get_order_details(order_id)['Prc'])
                            break
                        except:
                            cntr += 1
                            sleep(0.5)
                    conn.commit()
                    
                else:
                    order_id = randint(1,1000)
                    placed_price = ltp
                log_interface.postLog(severity='INFO',message='Placed BP WEALTH options order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1)
                
            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place BP WEALTH options order. User: {}. Tradingsymbol:{}. QTY:{} .'.format(username,tradingsymbol,qty*lot_size),publish = 1, tag = 'OMSB_OP_1')
                order_id = -1
                placed_price = LTP_Table[str(instrument_token)]
        else:
            #Futures
            try:
                ltp = LTP_Table[str(instrument_token)]
            except Exception as e:
                print('123 LTP not found for instrument token:{}'.format(instrument_token))
                print(e)
                return
    
            if qty > 0:
                price = ltp*1.01
            else:
                price = ltp*0.99
            price = myround(price,0.5)
            price = price*100
            try:
                if paper_trade == False:
                    if transaction_type == 'BUY':
                        buy_sell = '1'
                    else:
                        buy_sell = '2'
                    # get orde_price from order book using username, tradingsymbol, qty, transaction_type
                    order_details, order_id = brokerage_object.place_order(position=transaction_type, scriptkn=exchange_token, instrument="FUTIDX", symbol=symbol, buysell=buy_sell, org_qty=abs(lot_size*qty), ord_price=price)
                    sleep(1)
                    sleep(1)
                    cntr = 0
                    while cntr < 10:
                        try:
                            placed_price = float(brokerage_object.get_order_details(order_id)['Prc'])
                            break
                        except:
                            cntr += 1
                            sleep(0.5)
                    conn.commit()
                
                else:
                    order_id = randint(1,1000)
                    placed_price = LTP_Table[str(instrument_token)]
                
                log_interface.postLog(severity='INFO',message='Placed BP WEALTH futures order for:{}, instrument:{}, qty:{}, transaction type:{}, placed price:{}, id:{}.'.format(username,tradingsymbol,qty*lot_size, transaction_type,placed_price, order_id), publish=1)
                
            except:
                log_interface.postLog(severity="CRITICAL",message='Failed to place BP WEALTH futures order. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_2')
                order_id = -1
                placed_price = LTP_Table[str(instrument_token)]
        try:
            update_order_placement(username=username,tradingsymbol=tradingsymbol,placed_qty=qty,placed_price=placed_price, spread_list=spread_list, brokerage_name=user_type, brokerage_id=order_id, debug=debug) # If this fails, infinite order placement -> stop this thread + critical user message
        except:
            # kill the thread to avoid infinite order placement
            log_interface.postLog(severity="CRITICAL",message='Failed to update order placement in DB. User: {}. Tradingsymbol:{}. QTY:{}.'.format(username,tradingsymbol, qty*lot_size),publish = 1, tag = 'OMSB_OP_3')
            return True
    # close connection
    conn.commit()
    return
