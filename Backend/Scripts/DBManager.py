#Testing accessing a database through many strings

import threading
import sqlite3
from sqlite3 import Connection, Cursor
import time
from datetime import datetime
from OMS_API_Interface import OMS_Interface
from Log_Server_Interface import Log_Server_Interface
import json
import time

def addToOrderHistory(cur,order_id, brokerage_id, user_type,  username, strategy_name, tradingsymbol, position, instrument_nomenclature, order_price, order_qty, lot_size, order_time, order_status=None):
    cur.execute("INSERT INTO order_history (order_id, brokerage,brokerage_id,  username, strategy_name, tradingsymbol, position, instrument_nomenclature, order_status, order_price, order_qty, order_time) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",(order_id,brokerage_id, user_type ,username, strategy_name, tradingsymbol, position, instrument_nomenclature, 'COMPLETE', order_price, order_qty*lot_size, order_time))

def measure_performance(func):
  def wrapper(*args, **kwargs):
    start_time = time.perf_counter()
    result = func(*args, **kwargs)
    end_time = time.perf_counter()
    print(f"{func.__name__} took {end_time - start_time:.6f} seconds to complete")
    return result
  return wrapper

def get_new_dbconnection():
    con = sqlite3.connect('../../C/Data/OrderData.db')
    return con

def gSF(stringToConvert: str):
    '''
    Converts string to a format acceptable by sqlite3 for text type entries.
    
    Arguments:
    stringToConvert {str} -- The string to convert

    Keyword Arguments:
    None

    Returns:
    converted string {str} - The string converted to the needed format.
    '''
    if type(stringToConvert) != type("string"):
        return "Invalid input type!"
    return "\'"+stringToConvert+"\'"


def addOrderToOrderBuffer(username, tradingsymbol, lot_size, exchange_token, quantity, strategy_name, instrument_nomenclature, position,exchange,segment, instrument_token, cur, rollover = 'N'):
    """ 
    This function adds the order to the orderbuffer table in the database and returns True if successful.

    Parameters:
    username (str): Username of the user
    tradingsymbol (str): Tradingsymbol of the instrument
    lot_size (int): Lot size of the instrument
    exchange_token (int): Exchange token of the instrument
    quantity (int): Quantity of the instrument
    strategy_name (str): Strategy name of the order
    instrument_nomenclature (str): Instrument nomenclature of the order
    position (str): Position of the order to be taken

    Returns:
    bool: True if successful, False otherwise

    Keywork Arguments:
    None
    """
    try:
        cur.execute('SELECT * FROM orderbuffer WHERE username = {} and tradingsymbol = {}'.format(gSF(username),gSF((tradingsymbol))))
        res = cur.fetchall()
    except sqlite3.Error as e:
        print("Error while fetching data from orderbuffer: ", e)
        return False
    
    if len(res) == 0:
        #New position in orderbuffer
        position_id = str(hash(datetime.now()))
        try:
            cur.execute('INSERT INTO orderbuffer values ({}, {}, {}, {}, {}, {}, {}, {},{}, {}, {},{}, {})'.format(gSF(username),gSF(tradingsymbol),gSF(str(instrument_token)),lot_size, gSF(exchange),gSF(segment),exchange_token,quantity,0,0,0,position_id, gSF(rollover)))
        except sqlite3.Error as e:
            print("Error while adding to orderbuffer: ", e)
            return False
        
    else:
        #Position already exists
        position_id = list(res[0])[10]
        print("SELLING, qty={}".format(quantity))
        try:
            cur.execute('UPDATE orderbuffer SET total_qty = total_qty + {} WHERE username = {} and tradingsymbol = {};'.format(quantity, gSF(username),gSF(tradingsymbol)))
        except sqlite3.Error as e:
            print("Error while updating orderbuffer: ", e)
            return False
        
    return addOrderToPositionReference(position_id=position_id, strategy_name = strategy_name, instrument_nomenclature = instrument_nomenclature, position_type = position, username = username, cur=cur)

def addOrderToPositionReference(position_id, strategy_name, instrument_nomenclature, position_type, username, cur):
    """ 
    This function adds the order to the position reference table in the database and returns True if successful.

    Parameters:
    position_id (str): Position ID of the order
    strategy_name (str): Strategy name of the order
    instrument_nomenclature (str): Instrument nomenclature of the order
    position_type (str): Position of the order to be taken
    username (str): Username of the user

    Returns:
    bool: True if successful, False otherwise

    Keywork Arguments:
    None
    """
    try:
        cur.execute('INSERT INTO position_reference values ({}, {}, {}, {}, {})'.format(position_id,gSF(strategy_name),gSF(instrument_nomenclature),gSF(position_type),gSF(username)))
        return True
    except sqlite3.Error as e:
        print("Error while adding to position reference : {}".format(e))
        return False

def update_LTP(instrument_token:int, LTP:float):
    db_connection = get_new_dbconnection()
    #Call tickwise
    cur = db_connection.cursor()
    cur.execute('UPDATE order_reference SET position_value = {} - position_entry_price WHERE instrument_token = {} and position_type = {} and position_status = {};'.format(LTP,instrument_token,gSF('BUY'),gSF('PLACED')))
    cur.execute('UPDATE order_reference SET position_value = position_entry_price - {} WHERE instrument_token = {} and position_type = {} and position_status = {};'.format(LTP,instrument_token,gSF('OPEN SHORT'),gSF('PLACED')))
    db_connection.commit()
    check_position_stoploss()


# @measure_performance
def update_LTP_peg(peg:str, LTP:float):
    db_connection = get_new_dbconnection()
    #Call tickwise
    cur = db_connection.cursor()
    with open('../Data/LTP_table.json') as f:
        ltp_table = json.load(f)
    if peg == 'NIFTY':
        ltp = ltp_table['256265']
    else:
        ltp = ltp_table['260105']
    cur.execute('UPDATE orderbook SET net_position_value = {} - net_entry_price WHERE index_peg = {} and position = {} and order_status = {};'.format(ltp,gSF(peg),gSF('BUY'),gSF('PLACED')))
    cur.execute('UPDATE orderbook SET net_position_value = net_entry_price - {} WHERE index_peg = {} and position = {} and order_status = {};'.format(ltp,gSF(peg),gSF('OPEN SHORT'),gSF('PLACED')))
    db_connection.commit()
    check_position_stoploss()


def check_position_stoploss():
    db_connection = get_new_dbconnection() 
    cur = db_connection.cursor()
    cur.execute("SELECT * FROM order_reference WHERE position_value < position_stoploss and position_stoploss > 0 and position_status = {};".format(gSF('PLACED')))
    #print(cur.fetchall())


def get_days_to_expiry(expiry:str, instrument_nomenclature:str):
    return 2


def check_rollovers(oms_interface: OMS_Interface):
    db_connection = get_new_dbconnection() 
    cur = db_connection.cursor()
    cur.execute("SELECT order_id, expiry_date, position_type, instrument_nomenclature FROM order_reference WHERE position_status = {};".format(gSF('PLACED')))
    positions = cur.fetchall()
    for p in positions:
        order_id = list(p)[0]
        expiry_date = list(p)[1]
        position_type = list(p)[2]
        instrument_nomenclature = list(p)[3]
        if get_days_to_expiry(expiry_date, instrument_nomenclature) <= 2:
            cur.execute('UPDATE order_reference SET position_status = {} WHERE order_id = {} and instrument_nomenclature = {};'.format(gSF("ROLLOVER"),order_id,gSF(instrument_nomenclature)))
            cur.execute('UPDATE orderbook SET order_status = {} WHERE order_id = {};'.format(gSF('ROLLOVER'),order_id))
            db_connection.commit()


def check_net_stoploss_target(log_interface: Log_Server_Interface):
    # print("CALLED")
    '''
    order = {
        "ORDERS":[
            {
                "STRATEGY": "NOVA",
                "INSTRUMENT_NOMENCLATURE": "SPREAD_TEST",
                "POSITION":"BUY",
                "TARGET":0.01,
                "STOPLOSS":0.01
            
            }
        ]
    }
    '''
    db_connection = get_new_dbconnection() 
    cur = db_connection.cursor()
    cur.execute("SELECT order_id, username, strategy_name, position, instrument_nomenclature, net_position_value FROM orderbook WHERE ((net_position_value < net_stoploss_value and net_stoploss_value != 0) or (net_position_value > net_target_value and net_target_value != 0)) and order_status = {};".format(gSF('PLACED')))
    positions = cur.fetchall()
    for p in positions:
        order_id = list(p)[0]
        username = list(p)[1]
        strategy_name = list(p)[2]
        instrument_nomenclature = list(p)[4]
        net_position_value = list(p)[5]
        if net_position_value < 0:
            log_interface.postLog(severity='INFO',message='STOPLOSS HIT FOR USER:{} STRATEGY:{} INSTRUMENT:{}.'.format(username,strategy_name,instrument_nomenclature),publish=1)
        if net_position_value > 0:
            log_interface.postLog(severity='INFO',message='TARGET HIT FOR USER:{} STRATEGY:{} INSTRUMENT:{}.'.format(username,strategy_name,instrument_nomenclature),publish=1)

        cur.execute("UPDATE orderbook SET order_status = {} WHERE order_id = {};".format(gSF('CLOSING'),order_id))
        cur.execute('SELECT quantity, exchange, segment, exchange_token, tradingsymbol, instrument_token, lot_size, position_type FROM order_reference WHERE order_id = {};'.format(order_id))
        references = cur.fetchall()
        cur.execute('UPDATE order_reference SET position_status = {} WHERE order_id = {};'.format(gSF('CLOSING'),order_id))
        for r in references:
            quantity = list(r)[0]
            exchange = list(r)[1]
            segment = list(r)[2]
            exchange_token = list(r)[3]
            tradingsymbol = list(r)[4]
            instrument_token = list(r)[5]
            lot_size = list(r)[6]
            position_type = list(r)[7]
            if position_type == 'BUY':
                position_type = 'SELL'
            if position_type == 'OPEN SHORT':
                position_type = 'CLOSE SHORT'
            addOrderToOrderBuffer(username=username,tradingsymbol=tradingsymbol, lot_size=lot_size, exchange_token=exchange_token,quantity=quantity*-1,strategy_name=strategy_name,instrument_nomenclature=instrument_nomenclature, position=position_type,exchange=exchange,segment=segment,instrument_token=instrument_token,cur=cur)
        db_connection.commit()
    
    


def get_stoploss(username: str):
    db_connection = get_new_dbconnection()
    cur = db_connection.cursor()
    cur.execute("SELECT")

def update_net_position_values(log_interface: Log_Server_Interface):
    db_connection = get_new_dbconnection()
    #Current paradigm: Call every 1s
    cur = db_connection.cursor()
    cur.execute("SELECT * from orderbook;")
    orders = cur.fetchall()

    for o in orders:
        order = list(o)
        order_status = order[0]
        if order_status != 'PLACED':
            continue
        order_id = order[-2]
        cur.execute('SELECT SUM(position_value) from order_reference WHERE order_id = {};'.format(order_id))
        position_value = list(list(cur.fetchall())[0])[0]
        cur.execute('UPDATE orderbook set net_position_value = {} WHERE order_id = {} and index_peg = {};'.format(position_value,order_id,gSF('N')))
        cur.execute('UPDATE orderbook set net_position_value = {} WHERE order_id = {} and index_peg = {};'.format(position_value,order_id, gSF('N')))
        db_connection.commit()
    check_net_stoploss_target(log_interface=log_interface)

def get_held_instruments(db_connection: Connection):
    cur = db_connection.cursor()
    


def get_pending_orders(username:str):
    db_connection = get_new_dbconnection()
    cur = db_connection.cursor()
    cur.execute('SELECT tradingsymbol, exchange_token, lot_size, total_qty, placed_qty, last_order_placement, exchange, segment, instrument_token from orderbuffer WHERE username = {} and (total_qty!=placed_qty or total_qty == 0);'.format(gSF(username)))
    orders = cur.fetchall()
    order_list = []
    for o in orders:
        dict = {}
        order = list(o)
        #print(order)
        dict['tradingsymbol'] = order[0]
        dict['exchange_token'] = order[1]
        dict['lot_size'] = order[2]
        dict['total_qty'] = order[3]
        dict['placed_qty'] = order[4]
        dict['last_placement'] = order[5]
        dict['exchange'] = order[6]
        dict['segment'] = order[7]
        dict['instrument_token'] = order[8]
        order_list.append(dict)
    return order_list


def update_orderbook_status(order_id:int,cur: Cursor, debug: bool = False):
    if debug:
        print('Updating orderbook status for order_id:{}'.format(order_id))

    position = cur.execute('SELECT position_status, position_entry_price, quantity, lot_size,position_type from order_reference WHERE order_id = {};'.format(order_id)).fetchall()
    #If it's a sell order and all legs/positions are sold
    if len(position) == 0:
        # Delete from orderbook table
        cur.execute('DELETE FROM orderbook WHERE order_id = {};'.format(order_id))
        return
    #If it's a buy
    order_placed = True
    net_position_value = 0
    net_lots = 0
    index_peg = list(list(cur.execute("SELECT index_peg from orderbook WHERE order_id = {};".format(order_id)).fetchall())[0])[0]
    
    for pos_tuple in position:
        position_status = list(pos_tuple)[0]
        if index_peg == 'N':
            position_entry_price = list(pos_tuple)[1]
            quantity = list(pos_tuple)[2]
            lot_size = list(pos_tuple)[3]
            position_type = list(pos_tuple)[4]
            if position_type == 'OPEN SHORT':
                net_position_value += position_entry_price*quantity*lot_size
            else:
                net_position_value += position_entry_price*quantity*lot_size
            net_lots += abs(quantity*lot_size)

        else:
            while True:
                with open('../Data/LTP_table.json') as f:
                    try:
                        ltp_table = json.load(f)
                        break
                    except:
                        pass
                time.sleep(0.01)
            if index_peg == 'NIFTY':
                position_entry_price = ltp_table['256265']
                lot_size = 50
                
            else:
                position_entry_price = ltp_table['260105']
            
            net_position_value = position_entry_price
            print(net_position_value)


        if position_status != 'PLACED':
            order_placed = False
    if order_placed:
        if index_peg == 'N':
            entry_price = net_position_value/net_lots
        else:
            entry_price = net_position_value
        cur.execute("UPDATE orderbook set order_status = {}, net_entry_price = {}, net_stoploss_value = net_stoploss_perc/100*{}*-1, net_target_value = net_target_perc/100*{} WHERE order_id = {};".format(gSF('PLACED'),entry_price,abs(entry_price),abs(entry_price),order_id)) 
        


def update_orderbuffer(username:str, tradingsymbol: str, placed_qty: int, placed_price: float,conn: Connection, cur: Cursor,spread_list: dict, brokerage_name : str, brokerage_id : int,debug: bool = False):
    #Get corresponding positions from the order buffer
    #We need position id, placed qty, total qty, placed price
    #Position ID is used to reference the position reference
    #placed, total qty are used to verify order completion, and the new order placement price
    cur.execute('SELECT position_id, placed_qty, total_qty, placed_price, rollover from orderbuffer WHERE username = {} AND tradingsymbol = {};'.format(gSF(username),gSF(tradingsymbol)))
    c = cur.fetchall()

    if debug:
        print('CALLED UPDATE ORDERBUFFER')
    
    position_id = list(c[0])[0]
    existing_qty = list(c[0])[1]
    total_qty = list(c[0])[2]
    existing_price = list(c[0])[3]
    rollover = list(c[0])[4]
    order_completion = False
    print("EQ:{} PQ:{} TQ:{}".format(existing_qty, placed_qty,total_qty))
    if existing_qty + placed_qty == total_qty:
        
        print("ORDER IS COMPLETE")
        order_completion = True
    print(order_completion)
    print("__________________")
    print(placed_price)
    print(type(placed_price))
    print(placed_qty)
    print(type(placed_qty))
    print(existing_price)
    print(type(existing_price))
    print(existing_qty)
    print(type(existing_qty))
    print("__________________")
    placed_price = float(placed_price)
    new_placement_price = (placed_price*placed_qty+existing_price*existing_qty)/(placed_qty+existing_qty) #The new average price
    
    cur.execute("UPDATE orderbuffer SET placed_qty = placed_qty + {}, placed_price = {}, last_order_placement = {} WHERE tradingsymbol = {} AND username = {};".format(placed_qty, new_placement_price, gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), gSF(tradingsymbol),gSF(username)))
    
    #Go to position reference where position id 
    cur.execute("SELECT strategy_name, instrument_nomenclature, position_type from position_reference where position_id = {};".format(position_id))
    c = cur.fetchall()

    positions_list = []
    for o in c:
        order_details = list(o)
        strategy_name = order_details[0]
        instrument_nomenclature = order_details[1]
        position_type = order_details[2]
        positions_list.append({'STRATEGY':strategy_name, 'INSTRUMENT_NOMENCLATURE':instrument_nomenclature,'TRADINGSYMBOL':tradingsymbol,'POSITION':position_type})
    
    #Empty orderbuffer if placed
    if total_qty == placed_qty + existing_qty:


        ########### ###########
        # ADD TO ORDER HISTORY#

        """ 
        requirements : 
        FETCH
        order_id : ORDER BOOK
        strategy_name, instrument_nomenclature, position_type : POSITION_REFERENCE
        instrument_nomenclature(of the leg) : ORDER_REFERENCE 
        lot_size : ORDERBUFFER
        
        READY TO USE
        placed_qty, tradingsymbol, username, brokerage_id, brokerage_name, order_price (placed_price) : passed through DBManager functions
        order_time : added in function (datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        """

        ######################
        # Fetch from POSITION_REFERENCE
        # use : position_id
        # get : strategy_name, position_type, instrument_nomenclature
        ######################
        cur.execute("SELECT strategy_name, position_type, instrument_nomenclature from position_reference where position_id = {};".format(position_id))
        c = cur.fetchall()
        strategy = list(c[0])[0]
        position_type = list(c[0])[1]
        instrument_nomenclature = list(c[0])[2]


        ######################
        # Fetch from ORDERBOOK
        # use : username, strategy_name, instrument_nomenclature
        # get : order_id
        ######################
        cur.execute("SELECT order_id from orderbook where username = {} AND strategy_name = {} AND instrument_nomenclature = {};".format(gSF(username),gSF(strategy),gSF(instrument_nomenclature)))
        c = cur.fetchall()
        order_id = list(c[0])[0]


        ######################
        # Fetch from ORDER_REFERENCE
        # use : order_id, tradingsymbol
        # get : instrument_nomenclature(of the leg), lot_size
        # issue : tradingsymbol changes for each leg when rollover function is called in API, thus refering using tradingsymbol for old data to close the leg is not possible, hence we need to use instrument_nomenclature
        ######################
        cur.execute("SELECT instrument_nomenclature from order_reference where order_id = {} AND tradingsymbol = {};".format(order_id,gSF(tradingsymbol)))
        c = cur.fetchall()
        # instrument_nomenclature_leg = list(c[0])[0]

        
        ######################
        # Fetch from ORDERBUFFER
        # use : position_id
        # get : lot_size
        ######################
        cur.execute("SELECT lot_size, total_qty from orderbuffer where position_id = {};".format(position_id))
        c = cur.fetchall()
        lot_size = list(c[0])[0]
        total_qty = list(c[0])[1]


        ######################
        # Set position_type using total_qty from ORDERBUFFER
        if total_qty < 0:
            if position_type == 'BUY': # Closing a long position
                position_type_corrected = 'SELL'
            else:
                position_type_corrected = 'OPEN SHORT'
        else: # total_qty > 0
            if position_type == 'OPEN SHORT': # Closing a short position
                position_type_corrected = 'CLOSE SHORT'
            else:
                position_type_corrected = 'BUY'
        
        # Overriding position_type_corrected to 'SELL'/'CLOSE SHORT' if position_type is 'SELL'/'CLOSE SHORT' in position_reference (becasue this is a non-rollover order)
        if position_type == 'SELL' or position_type == 'CLOSE SHORT':
            position_type_corrected = position_type


        print("#"*20)
        print("position_type : {}".format(position_type))
        print("total_qty : {}".format(total_qty))
        print("position_type_corrected : {}".format(position_type_corrected))
        print("#"*20)

        ######################

        
        ######################
        addToOrderHistory(cur=cur,order_id=order_id, user_type=brokerage_name,brokerage_id=brokerage_id,username=username, strategy_name=strategy, tradingsymbol=tradingsymbol, position=position_type_corrected, instrument_nomenclature=instrument_nomenclature, order_price=new_placement_price, order_qty=placed_qty, lot_size=lot_size, order_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ######################

        # addToOrderHistory(cur=cur,order_id=order_id, user_type=brokerage_name,brokerage_id=brokerage_id,username=username, strategy_name=strategy, tradingsymbol=tradingsymbol, position=position_type, instrument_nomenclature=instrument_nomenclature(of the leg), order_price=new_placement_price, order_qty=quantity, lot_size=lot_size, order_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        ########### ###########



        
        
        cur.execute("DELETE FROM orderbuffer WHERE tradingsymbol = {} AND username = {};".format(gSF(tradingsymbol),gSF(username)))
        cur.execute("DELETE FROM position_reference WHERE position_id = {};".format(position_id))
    if rollover == 'N':
        update_order_reference(username=username, position_list=positions_list, placed_price=new_placement_price,order_completion=order_completion,conn=conn,cur=cur, spread_list=spread_list, rollover = rollover, debug=debug, brokerage_name = brokerage_name, brokerage_id = brokerage_id)

def update_order_reference(username: str, position_list: list, placed_price: float, order_completion: bool,conn : Connection, cur: Cursor, spread_list: dict, brokerage_name : str, brokerage_id : int,debug: bool = False, rollover = 'N'):
    print("UOR:{}".format(order_completion))
    if debug:
        print('CALLED UPDATE ORDER REFERENCE')

    for position in position_list:
        strategy_name = position['STRATEGY']
        instrument_nomenclature = position['INSTRUMENT_NOMENCLATURE']
        tradingsymbol = position['TRADINGSYMBOL']
        position_type = position['POSITION']
        traded_position = position_type
        
        if position_type == 'SELL':
            traded_position = 'BUY'
        if position_type == 'CLOSE SHORT':
            traded_position = 'OPEN SHORT'
        print(traded_position)
        if instrument_nomenclature in spread_list.keys() and traded_position == 'OPEN SHORT':
            traded_position = 'BUY'

        #Get order id from orderbook for order_reference
        #print('SELECT order_id FROM orderbook WHERE username={} AND strategy_name={} AND position={} AND instrument_nomenclature={};'.format(gSF(username),gSF(strategy_name),gSF(traded_position),gSF(instrument_nomenclature)))
        #print(list(cur.execute('SELECT order_id FROM orderbook WHERE username={} AND strategy_name={} AND position={} AND instrument_nomenclature={};'.format(gSF(username),gSF(strategy_name),gSF(traded_position),gSF(instrument_nomenclature))).fetchall()[0])[0])
        order_id = list(cur.execute('SELECT order_id FROM orderbook WHERE username={} AND strategy_name={} AND position={} AND instrument_nomenclature={};'.format(gSF(username),gSF(strategy_name),gSF(traded_position),gSF(instrument_nomenclature))).fetchall()[0])[0]
        
        #Go to position within order reference
        #Update position target, stoploss and entry price
        #Get position target and SL percent
        if rollover == 'N':
            cur.execute('SELECT position_target_percent, position_stoploss_percent FROM order_reference WHERE order_id = {} AND tradingsymbol = {};'.format(order_id, gSF(tradingsymbol)))
            target_perc, stoploss_perc = list(cur.fetchall()[0])
            target_price = 0
            stoploss_price = 0
            order_status = 'IN PROGRESS'
            
            #Get actual target, SL and status values
            target_price = ((target_perc)/100)*placed_price
            stoploss_price = ((stoploss_perc)/100)*placed_price*-1
            if order_completion:
                order_status = 'PLACED'
            #update the order reference
            print('UPDATE order_reference SET position_target = {}, position_stoploss = {}, position_entry_price = {}, position_status = {} WHERE order_id = {} and tradingsymbol = {};'.format(target_price,stoploss_price,placed_price,gSF(order_status),order_id,gSF(tradingsymbol)))
            cur.execute('UPDATE order_reference SET position_target = {}, position_stoploss = {}, position_entry_price = {}, position_status = {} WHERE order_id = {} and tradingsymbol = {};'.format(target_price,stoploss_price,placed_price,gSF(order_status),order_id,gSF(tradingsymbol)))

        


        if order_completion and (position_type == 'SELL' or position_type == 'CLOSE SHORT'):
            cur.execute('DELETE FROM order_reference WHERE order_id = {} and tradingsymbol = {};'.format(order_id, gSF(tradingsymbol)))

        if order_completion and (position_type == 'BUY' or position_type == 'OPEN SHORT'):
            order_status = 'PLACED'
            # # CLOSE POSITION | Add to order_history table below data (using fetch)
            # cur.execute('SELECT username, instrument_nomenclature, position, net_entry_price, quantity, strategy_name from orderbook WHERE order_id = {};'.format(order_id))
            # order_data = list(list(cur.fetchall())[0])
            # strategy = (order_data)[5]
            
            # cur.execute('SELECT lot_size, quantity, position_entry_price from order_reference WHERE order_id = {} and position_type = {};'.format(order_id,gSF(position_type)))
            # data = list(list(cur.fetchall())[0])
            # lot_size = (data)[0]
            # quantity = (data)[1]
            # entry_price = (data)[2]
            
            # addToOrderHistory(cur,order_id, brokerage_name,brokerage_id,username, strategy, tradingsymbol, position_type, instrument_nomenclature, entry_price, quantity, lot_size, time.time())
            cur.execute('UPDATE order_reference SET position_status = {} WHERE order_id = {} and tradingsymbol = {};'.format(gSF('PLACED'),order_id,gSF(tradingsymbol)))
        
        #Set orderbook order status
        
        update_orderbook_status(order_id=order_id,cur=cur, debug=debug)

        

def update_order_placement(username:str, tradingsymbol: str, placed_qty: int, placed_price: float, spread_list: dict,brokerage_name : str, brokerage_id : int, debug: bool = False):
    db_connection = get_new_dbconnection()
    cur = db_connection.cursor()
    #Add order to order buffer
    update_orderbuffer(username=username,tradingsymbol=tradingsymbol,placed_qty=placed_qty,placed_price=placed_price,conn=db_connection,cur=cur, spread_list= spread_list, debug=debug, brokerage_name=brokerage_name, brokerage_id=brokerage_id)
    db_connection.commit()



""" # CLOSE POSITION | Add to order_history table below data (using fetch)
        # Fetch order_id, using position_id from position_reference table get strategy_name, instrument_nomenclature, position_type -> orderbook table -> order_id
        data = list(list(cur.execute("SELECT strategy_name, instrument_nomenclature, username from position_reference where position_id = {};".format(position_id)).fetchall())[0])
        print('DATA (ORDER HISTORY!!!!): {}'.format(data))
        strategy_name_ = data[0]
        instrument_nomenclature_ = data[1]
        username_ = data[2]
        
        print("SELECT order_id from orderbook where strategy_name = {} and instrument_nomenclature = {} and username = {};".format(gSF(strategy_name_),gSF(instrument_nomenclature_),gSF(username_)))
        order_id = list(list(cur.execute("SELECT order_id from orderbook where strategy_name = {} and instrument_nomenclature = {} and username = {};".format(gSF(strategy_name_),gSF(instrument_nomenclature_),gSF(username_))).fetchall())[0])[0]



        print("ORDER ID: {}".format(order_id))
        cur.execute('SELECT username, instrument_nomenclature, position, net_entry_price, quantity, strategy_name from orderbook WHERE order_id = {};'.format(order_id))
        order_data = list(list(cur.fetchall())[0])
        strategy = (order_data)[5]

        # Fetch position_type
        print('SELECT position_type from position_reference WHERE position_id = {} and username = {} and strategy_name = {};'.format(position_id,gSF(username_),gSF(strategy)))
        cur.execute('SELECT position_type from position_reference WHERE position_id = {} and username = {} and strategy_name = {};'\
            .format(position_id,gSF(username),gSF(strategy)))
        position_type_new = list(list(cur.fetchall())[0])[0]
        
        

        cur.execute('SELECT total_qty from orderbuffer WHERE position_id = {};'.format(position_id))
        data = list(list(cur.fetchall())[0])
        total_qty = (data)[0]

        if total_qty < 0:
            if position_type_new == 'BUY':
                position_type_ = 'SELL'
            else:
                position_type_ = 'OPEN SHORT'
        else: # positive eg. 2
            if position_type_new == 'OPEN SHORT':
                position_type_ = 'CLOSE SHORT'
            else:
                position_type_ = 'BUY'

        print('SELECT lot_size, quantity, position_entry_price from order_reference WHERE order_id = {} and position_type = {};'.format(order_id,gSF(position_type_new)))
        cur.execute('SELECT lot_size, quantity, position_entry_price from order_reference WHERE order_id = {} and position_type = {};'.format(order_id,gSF(position_type_new)))
        data = list(list(cur.fetchall())[0])
        lot_size = (data)[0]
        quantity = (data)[1]
        entry_price = (data)[2]

        print('TRADINSYMBOL: {}'.format(tradingsymbol))
        print('TOTAL QTY: {}'.format(total_qty))
        print('POSITION TYPE: {}'.format(position_type_new))
        print('POSITION TYPE_: {}'.format(position_type_)) """