
from datetime import datetime
import json
import sqlite3
from sqlite3 import Connection, Cursor

def get_new_dbconnection():
    con = sqlite3.connect('../../OMS/Data/OrderData.db')
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


## HELPER FUNCTIONS
def update_orerbook_status(order_id:int,cur: Cursor):
    """ 
    Update the orderbook status for the order_id provided.

    Arguments:
    order_id {int} -- The order_id for which the status is to be updated.
    cur {Cursor} -- The cursor object for the database connection.

    Keyword Arguments:
    None

    Returns:
    None
    """

    try:
        position = cur.execute('SELECT position_status from order_reference WHERE order_id = {};'.format(order_id)).fetchall()
        #If it's a sell order then all legs/positions are(should) sold
        if len(position) == 0:
            cur.execute('DELETE FROM orderbook WHERE order_id = {};'.format(order_id))
            
        
        #If it's a buy, then all legs/positions are(should) be bought
        order_placed = True
        for pos_tuple in position:
            if list(pos_tuple)[0] != 'PLACED':
                order_placed = False
        if order_placed:
            cur.execute("UPDATE orderbook set order_status = {} WHERE order_id = {};".format(gSF('PLACED'),order_id)) 
    except Exception as e:
        print("Error in update_orerbook_status: "+str(e))
        

def update_order_reference(username: str, position_list: list, placed_price: float, order_completion: bool, cur: Cursor):
    """
    in OrderReference (via positonReference and orderBook),update the entry price, SL/Target (for the current order in placement).
    If order is complete, set order_status to complete | delete row from orderbook | delete row from positionReference
    Also update the orderbook order status.


    It get a list of positions from order_buffer table, and then iterates through each position, and updates the order_reference table.

    Arguments:
    username {str} -- The username of the user.
    position_list {list} -- The list of positions to be updated.
    placed_price {float} -- The price at which the order was placed.
    order_completion {bool} -- True if the order is complete, False otherwise.
    cur {Cursor} -- The cursor object for the database connection.

    Keyword Arguments:
    None

    Returns:
    None
    """
    
    try:
        print("Updating order_reference table")

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
            
            #Get order id from orderbook for order_reference
            order_id = list(cur.execute('SELECT order_id FROM orderbook WHERE username={} AND strategy_name={} AND position={} AND instrument_nomenclature={};'.format(gSF(username),gSF(strategy_name),gSF(traded_position),gSF(instrument_nomenclature))).fetchall()[0])[0]
            
            #Go to position within order reference
            #Update position target, stoploss and entry price
            #Get position target and SL percent
            target_perc, stoploss_perc = list(cur.execute('SELECT position_target_percent, position_stoploss_percent FROM order_reference WHERE order_id = {} AND tradingsymbol = {};'.format(order_id, gSF(tradingsymbol))).fetchall()[0])
            target_price = 0
            stoploss_price = 0
            order_status = 'IN PROGRESS'
            
            
            #Get actual target, SL values
            # TARGET
            if target_perc > 0 and position_type == 'BUY':
                target_price = ((100+target_perc)/100)*placed_price
            if target_perc > 0 and position_type == 'OPEN SHORT':
                target_price = ((100 - target_perc)/100)*placed_price

            # STOPLOSS
            if stoploss_perc > 0 and position_type == 'BUY':
                stoploss_price = ((100 - stoploss_perc)/100)*placed_price
            if stoploss_perc > 0 and position_type == 'OPEN SHORT':
                stoploss_price = ((100 + stoploss_perc)/100)*placed_price
            
            # Order completion check -> if order is complete, set order_status to complete, or delete row. Also update the orderbook order status.
            if order_completion:
                order_status = 'PLACED'
            
            
            #update the order reference
            cur.execute('UPDATE order_reference SET position_target = {}, position_stoploss = {}, position_entry_price = {}, position_status = {} WHERE order_id = {} and tradingsymbol = {};'.format(target_price,stoploss_price,placed_price,gSF(order_status),order_id,gSF(tradingsymbol)))

            # case when order is completed | for BUY and SELL condition
            if order_completion and position_type == 'SELL' or position_type == 'CLOSE SHORT':
                cur.execute('DELETE FROM order_reference WHERE order_id = {} and tradingsymbol = {};'.format(order_id, gSF(tradingsymbol)))
                # DEBUG
                # print("Deleting order_reference table for order_id: ", order_id, " and tradingsymbol: ", tradingsymbol)

            if order_completion and position_type == 'BUY' or position_type == 'OPEN SHORT':
                cur.execute('UPDATE order_reference SET position_status = {} WHERE order_id = {} and tradingsymbol = {};'.format(gSF('PLACED'),order_id,gSF(tradingsymbol)))
                # DEBUG
                # print("Updating order_reference table for order_id: ", order_id, " and tradingsymbol: ", tradingsymbol)
            
            update_orerbook_status(order_id=order_id, cur=cur)
    except Exception as e:
        print("Error in update_order_reference: ", str(e))

def update_order_buffer(username:str, tradingsymbol: str, placed_qty: int, placed_price: float, cur: Cursor):
    """ 
    Get position_id, placed_qty, total_qty WHERE username and tradingsymbol are same from order_buffer table.
    Update placed_qty and total_qty in order_buffer table (using data from brokerage API)

    Check for order completion -> if order is complete, set order_status to complete, or delete row. Also update the orderbook order status.

    Use position_id to get list of positions from order_buffer table that hold same tradingsymbol.
    Next : call update_order_reference function to update the order_reference table.
    """
    
    try:
        print("Updating order buffer (step 1): "+str(placed_qty))
        # Get position_id, placed_qty, total_qty WHERE username and tradingsymbol are same from order_buffer table.
        c = cur.execute('SELECT position_id, placed_qty, total_qty, placed_price from orderbuffer WHERE username = {} AND tradingsymbol = {};'.format(gSF(username),gSF(tradingsymbol))).fetchall()

        #DEBUG 
        # print("Order retrieved from orderbuffer (step 1): "+str(c))

        # Update placed_qty and total_qty in order_buffer table (using data from brokerage API)
        position_id = list(c[0])[0]
        existing_qty = list(c[0])[1]
        total_qty = list(c[0])[2]
        existing_price = list(c[0])[3]
        order_completion = False
        if existing_qty + placed_qty == total_qty:
            order_completion = True
        new_placement_price = (placed_price*placed_qty+existing_price*existing_qty)/(placed_qty+existing_qty) #The new average price
        
        
        print("New placement price (step2): "+str(new_placement_price))
        # Update orderbuffer table with new placement price and new placed_qty value
        cur.execute("UPDATE orderbuffer SET placed_qty = placed_qty + {}, placed_price = {}, last_order_placement = {} WHERE tradingsymbol = {} AND username = {};".format(placed_qty, new_placement_price, gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S')), gSF(tradingsymbol),gSF(username)))
        

        # Data collection for the next table (from orderbuffer -> to positon reference)
        # Go to position reference where position id 
        c = cur.execute("SELECT strategy_name, instrument_nomenclature, position_type from position_reference where position_id = {};".format(position_id)).fetchall()

        
        # Creating list of positions (acc. to tradingsymbol)
        positions_list = []
        for o in c:
            order_details = list(o)
            # To refer to order_book
            strategy_name = order_details[0]
            instrument_nomenclature = order_details[1]
            position_type = order_details[2]
            positions_list.append({'STRATEGY':strategy_name, 'INSTRUMENT_NOMENCLATURE':instrument_nomenclature,'TRADINGSYMBOL':tradingsymbol,'POSITION':position_type})
        print("Positions to be updated in orderbook and order_reference (Step 4): "+str(positions_list))
        
        # CHECKPOINT
        #Empty orderbuffer if placed
        if total_qty == placed_qty + existing_qty:
            cur.execute("DELETE FROM orderbuffer WHERE tradingsymbol = {} AND username = {};".format(gSF(tradingsymbol),gSF(username)))
            cur.execute("DELETE FROM position_reference WHERE position_id = {};".format(position_id))
            print("Order completed. Deleted from orderbuffer and position_reference")
        update_order_reference(username=username, position_list=positions_list, placed_price=new_placement_price,order_completion=order_completion,cur=cur)
    except Exception as e:
        print("Error in update_order_buffer: ", str(e))






if __name__ == "__main__":

    ## Testing the function
    conn = sqlite3.connect('../Data/OrderData.db')
    cur = conn.cursor()

    today = datetime.now().date()
    query = f"SELECT order_time,instrument_nomenclature, tradingsymbol, order_price, position  FROM order_history WHERE DATE(order_time) = '2023-05-09'" 
    print(query)
    cur.execute(query)
    slippage_report = cur.fetchall()
    print(slippage_report)

    data = []

    for row in slippage_report:
        data.append({
            'end_date': row[0],
            'instrument_nomenclature': row[1],
            'trading_symbol': row[2],
            'price': row[3],
            'position': row[4]
        })
    
    # pretty print data
    print(json.dumps(data, indent=4, sort_keys=True))


    # Query for deleting all the tables (for testing) and reinitializing
    # cur.execute("DROP TABLE order_reference;")
    # cur.execute("DROP TABLE orderbook;")
    # cur.execute("DROP TABLE orderbuffer;")
    # cur.execute("DROP TABLE position_reference;")
    # cur.execute("DROP TABLE order_history;")
    # # cur.execute("DROP TABLE strategy_history;")
    

    # cur.execute('CREATE TABLE IF NOT EXISTS orderbook ('\
    #     'order_status text NOT NULL,'\
    # 	'username text NOT NULL,'\
    # 	'strategy_name text NOT NULL,'\
    #     'instrument_nomenclature text NOT NULL,'\
    #     'position text NOT NULL,'\
    #     'quantity integer NOT NULL,'\
    #     'net_entry_price real NOT NULL DEFAULT 0,'\
    #     'net_stoploss_perc real NOT NULL,'\
    #     'net_target_perc real NOT NULL,'\
    #     'net_stoploss_value real NOT NULL DEFAULT 0,'\
    #     'net_target_value real NOT NULL DEFAULT 0,'\
    #     'net_position_value real NOT NULL DEFAULT 0,'\
    # 	'order_id integer NOT NULL PRIMARY KEY,'\
    # 	'index_peg text DEFAULT "N" NOT NULL'\
    # ');')

    # cur.execute('CREATE TABLE IF NOT EXISTS order_reference ('\
    # 	'order_id integer NOT NULL,'\
    #     'position_status text NOT NULL,'\
    # 	'entry_datetime text NOT NULL,'\
    #     'quantity integer NOT NULL,'\
    #     'expiry_date text NOT NULL,'\
    #     'exchange text NOT NULL,'\
    #     'segment text NOT NULL,'\
    #     'exchange_token integer NOT NULL,'\
    #     'tradingsymbol text NOT NULL,'\
    #     'instrument_token text NOT NULL,'\
    #     'lot_size integer NOT NULL,'\
    #     'position_stoploss_percent real NOT NULL,'\
    #     'position_target_percent real NOT NULL,'\
    #     'position_stoploss real NOT NULL  DEFAULT 0,'\
    #     'position_target real NOT NULL  DEFAULT 0,'\
    #     'position_entry_price real NOT NULL  DEFAULT 0,'\
    #     'position_value real NOT NULL  DEFAULT 0,'\
    #     'position_type real NOT NULL  DEFAULT 0,'\
    #     'instrument_nomenclature real NOT NULL,'\
    #     'FOREIGN KEY (order_id) REFERENCES orderbook (order_id) ON DELETE CASCADE' 
    # ');')

    # cur.execute('CREATE TABLE IF NOT EXISTS orderbuffer ('\
    # 	'username text NOT NULL,'\
    # 	'tradingsymbol text NOT NULL,'\
    # 	'instrument_token text NOT NULL,'\
    #     'lot_size integer NOT NULL,'\
    #     'exchange text NOT NULL,'\
    #     'segment text NOT NULL,'\
    #     'exchange_token integer NOT NULL,'\
    #     'total_qty integer NOT NULL,'\
    #     'placed_qty integer NOT NULL,'\
    #     'placed_price integer NOT NULL,'\
    #     'last_order_placement text NOT NULL,'\
    #     'position_id integer NOT NULL,'\
    #     'rollover text NOT NULL DEFAULT "N"'
    # ');')

    # cur.execute('CREATE TABLE IF NOT EXISTS position_reference ('\
    # 	'position_id integer NOT NULL,'\
    # 	'strategy_name text NOT NULL,'\
    #     'instrument_nomenclature text NOT NULL,'\
    #     'position_type text NOT NULL,'\
    #     'username text NOT NULL,'\
    #     'FOREIGN KEY (position_id)'\
    #         'REFERENCES orderbuffer (position_id)'\
    #         'ON DELETE CASCADE'
    # ');')
    
    # cur.execute('CREATE TABLE IF NOT EXISTS order_history ('\
    #     'order_id integer NOT NULL,'\
    #     'brokerage_id integer NOT NULL,'\
    #     'brokerage text NOT NULL,'\
    #     'username text NOT NULL,'\
    #     'strategy_name text NOT NULL,'\
    #     'tradingsymbol text NOT NULL,'\
    #     'position text NOT NULL,'\
    #     'instrument_nomenclature text NOT NULL,'\
    #     'order_status text NOT NULL,'\
    #     'order_price real NOT NULL,'\
    #     'order_qty integer NOT NULL,'\
    #     'order_time text NOT NULL'\
    # ');')
    
    # cur.execute('CREATE TABLE IF NOT EXISTS strategy_history ('\
    #     'order_id integer NOT NULL,'\
    #     'username text NOT NULL,'\
    #     'strategy_name text NOT NULL,'\
    #     'tradingsymbol text NOT NULL,'\
    #     'position text NOT NULL,'\
    #     'instrument_nomenclature text NOT NULL,'\
    #     'order_price real NOT NULL,'\
    #     'order_quantity integer NOT NULL,'\
    #     'order_datetime text NOT NULL'\
    # ');')

    # SAMPLE VALUE (order_reference) : -2225231794287368831	IN PROGRESS	2022-12-19 17:42:07	1	2022-12-29	10000	NIFTY16800PE	50	0.0	1.0	0.0	0.0	0.0
    # SAMPLE VALUE (orderbook) : CLOSING	FINVANT	NOVA	NIFTY	BUY	75	0.0	1.0	1.0	0.0	0.0	-7744856246554436579
    # SAMPLE VALUE (orderbuffer) : FINVANT	NIFTY16800PE	50	10000	0	0	0	-6475757014321858749
    # SAMPLE VALUE (position_reference) : -6475757014321858749	NOVA	SPREAD123	BUY	FINVANT

    # Query for clearing all the tables (for testing) and reinitializing
    # cur.execute("DELETE FROM order_reference;")
    # cur.execute("DELETE FROM orderbook;")
    # cur.execute("DELETE FROM orderbuffer;")
    # cur.execute("DELETE FROM position_reference;")
    # cur.execute("DELETE FROM order_history;")
    # cur.execute("DELETE FROM strategy_history;")


    # Query for inserting values for sample order
    # cur.execute("INSERT INTO order_reference VALUES (-7744856246554436579,'IN PROGRESS',{},2,'2022-12-29',10000,'NIFTY16800PE',1,0.0,0.0,0.0,0.0,0.0);".format(gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    # cur.execute("INSERT INTO orderbook VALUES ('IN PROGRESS','FINVANT','NOVA','NIFTY','BUY',2,0.0,1.0,1.0,0.0,0.0,18901,-7744856246554436579);")
    # cur.execute("INSERT INTO orderbuffer VALUES ('FINVANT','NIFTY16800PE',1,10000,2,0,0,0,-6475757014321858749);")
    # cur.execute("INSERT INTO position_reference VALUES (-6475757014321858749,'NOVA','NIFTY','BUY','FINVANT');")


    # Query for sell order conditions
    # cur.execute("INSERT INTO order_reference VALUES (-7744856246554436579,'CLOSING',{},2,'2022-12-29',10000,'NIFTY16800PE',1,0.0,0.0,0.0,0.0,1865,18901);".format(gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    # cur.execute("INSERT INTO orderbook VALUES ('CLOSING','FINVANT','NOVA','NIFTY','BUY',2,0.0,1.0,1.0,0.0,0.0,18901,-7744856246554436579);")
    # cur.execute("INSERT INTO orderbuffer VALUES ('FINVANT','NIFTY16800PE',1,10000,-2,0,0,0,-6475757014321858749);")
    # cur.execute("INSERT INTO position_reference VALUES (-6475757014321858749,'NOVA','NIFTY','BUY','FINVANT');")

    # Query for a spread buy order conditions
    # cur.execute("INSERT INTO orderbook VALUES ('IN PROGRESS','FINVANT','NOVA','SPREAD_1','BUY',1,0.0,1.0,1.0,0.0,0.0,29.5,-7744856246554436579);")
    # cur.execute("INSERT INTO order_reference VALUES (-7744856246554436579,'IN PROGRESS',{},1,'2022-12-29',10000,'NIFTY16800PE',1,0.0,0.0,0.0,0.0,1865,18901);".format(gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    # cur.execute("INSERT INTO order_reference VALUES (-7744856246554436579,'IN PROGRESS',{},1,'2022-12-29',10001,'NIFTY17000PE',1,0.0,0.0,0.0,0.0,1865,18902);".format(gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
    # cur.execute("INSERT INTO orderbuffer VALUES ('FINVANT','NIFTY16800PE',1,10000,1,0,0,0,-6475757014321858749);")
    # cur.execute("INSERT INTO orderbuffer VALUES ('FINVANT','NIFTY17000PE',1,10001,1,0,0,0,-6475757014321858750);")
    # cur.execute("INSERT INTO position_reference VALUES (-6475757014321858749,'NOVA','SPREAD_1','BUY','FINVANT');")
    # cur.execute("INSERT INTO position_reference VALUES (-6475757014321858750,'NOVA','SPREAD_1','BUY','FINVANT');")

    # sample entry for order_reference
    # cur.execute("INSERT INTO order_reference VALUES (-7744856246554436579,'IN PROGRESS',{},2,'2022-12-29','NFO','NFO-OPT',10000,'NIFTY','NIFTY16802PE',1,0.0,0.0,0.0,0.0,1865,18901, 'N', 'N|N');".format(gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))


    # Query to assist in converting buy order to completed order -> to close it
    # cur.execute("UPDATE orderbook SET order_status='PLACED';")
    # cur.execute("UPDATE order_reference SET position_status='PLACED';")

    
    # SELL ORDER
    # update_order_buffer(username='FINVANT', tradingsymbol='NIFTY16800PE', placed_qty=-1, placed_price=18000, cur=cur)
    # BUY ORDER
    # update_order_buffer(username='FINVANT', tradingsymbol='SPREAD_1', placed_qty=1, placed_price=18000, cur=cur)
    conn.commit()