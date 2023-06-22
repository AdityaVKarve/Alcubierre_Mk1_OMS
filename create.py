'''
username: admin
password: FinvantResearch
port: 3306
endpoint: database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com
'''
from datetime import datetime
import pymysql

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

db = pymysql.connect(host="database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com",user="admin",password="FinvantResearch" ,db="test")
cursor = db.cursor()


# query = 'DROP TABLE orderbook'
# cursor.execute(query)
# print(cursor.fetchall())

# cursor.execute('CREATE TABLE IF NOT EXISTS slippage ('\
#                 'order_time text NOT NULL,'\
#                 'instrument_nomenclature text NOT NULL,'\
#                 'Close_5M integer NOT NULL,'\
#                 'Entry_Exit integer NOT NULL,'\
#                 'slippage integer NOT NULL,'\
#                 'username text NOT NULL,'\
#                 'brokerage text NOT NULL,'\
#                 'position text NOT NULL,'\
#                 'vix_close integer NOT NULL,'\
#                 'slippage_points integer NOT NULL'\
#             ');')

# cursor.execute('CREATE TABLE IF NOT EXISTS orderbook ('\
#         'order_status text NOT NULL,'\
#     	'username text NOT NULL,'\
#     	'strategy_name text NOT NULL,'\
#         'instrument_nomenclature text NOT NULL,'\
#         'position text NOT NULL,'\
#         'quantity integer NOT NULL,'\
#         'net_entry_price real NOT NULL DEFAULT 0,'\
#         'net_stoploss_perc real NOT NULL,'\
#         'net_target_perc real NOT NULL,'\
#         'net_stoploss_value real NOT NULL DEFAULT 0,'\
#         'net_target_value real NOT NULL DEFAULT 0,'\
#         'net_position_value real NOT NULL DEFAULT 0,'\
#     	'order_id BIGINT NOT NULL PRIMARY KEY,'\
#     	'index_peg varchar(20) DEFAULT "N" NOT NULL'\
#     ');')

# cursor.execute("INSERT INTO orderbook VALUES ('IN PROGRESS','FINVANT','NOVA','NIFTY','BUY',2,0.0,1.0,1.0,0.0,0.0,18901,-7744856246554436579,'N');")

# query = 'select * from orderbook'
# cursor.execute(query)
# print(cursor.fetchall())

# query = 'DROP TABLE order_reference'
# cursor.execute(query)
# print(cursor.fetchall())

# cursor.execute('CREATE TABLE IF NOT EXISTS order_reference ('\
#     	'order_id BIGINT NOT NULL,'\
#         'position_status text NOT NULL,'\
#     	'entry_datetime text NOT NULL,'\
#         'quantity integer NOT NULL,'\
#         'expiry_date text NOT NULL,'\
#         'exchange text NOT NULL,'\
#         'segment text NOT NULL,'\
#         'exchange_token integer NOT NULL,'\
#         'tradingsymbol text NOT NULL,'\
#         'instrument_token text NOT NULL,'\
#         'lot_size integer NOT NULL,'\
#         'position_stoploss_percent real NOT NULL,'\
#         'position_target_percent real NOT NULL,'\
#         'position_stoploss real NOT NULL  DEFAULT 0,'\
#         'position_target real NOT NULL  DEFAULT 0,'\
#         'position_entry_price real NOT NULL  DEFAULT 0,'\
#         'position_value real NOT NULL  DEFAULT 0,'\
#         'position_type real NOT NULL  DEFAULT 0,'\
#         'instrument_nomenclature real NOT NULL,'\
#         'FOREIGN KEY (order_id) REFERENCES orderbook (order_id) ON DELETE CASCADE' 
#     ');')

# cursor.execute("INSERT INTO order_reference VALUES (-7744856246554436579,'IN PROGRESS',{},2,'2022-12-29','NFO', 'NFO-OPT',10000,'NIFTY16800PE','11001',1,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0);".format(gSF(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))

# query = 'select * from order_reference'
# cursor.execute(query)
# print(cursor.fetchall())

# query = 'DROP TABLE orderbuffer'
# cursor.execute(query)

# cursor.execute('CREATE TABLE IF NOT EXISTS orderbuffer ('\
#     'username text NOT NULL,'\
#     'tradingsymbol text NOT NULL,'\
#     'instrument_token text NOT NULL,'\
#     'lot_size integer NOT NULL,'\
#     'exchange text NOT NULL,'\
#     'segment text NOT NULL,'\
#     'exchange_token integer NOT NULL,'\
#     'total_qty integer NOT NULL,'\
#     'placed_qty integer NOT NULL,'\
#     'placed_price integer NOT NULL,'\
#     'last_order_placement text NOT NULL,'\
#     'position_id BIGINT NOT NULL PRIMARY KEY,'\
#     'rollover varchar(20) DEFAULT "N" NOT NULL'
# ');')

# cursor.execute("INSERT INTO orderbuffer VALUES ('FINVANT','NIFTY16800PE','1292920',1,'exchange','segment',10000,-2,0,0,'0',-64757574,'N');")

# query = 'select * from orderbuffer'
# cursor.execute(query)
# print(cursor.fetchall())


# query = 'DROP TABLE position_reference'
# cursor.execute(query)
# print(cursor.fetchall())

# cursor.execute('CREATE TABLE IF NOT EXISTS position_reference ('\
#     	'position_id BIGINT NOT NULL,'\
#     	'strategy_name text NOT NULL,'\
#         'instrument_nomenclature text NOT NULL,'\
#         'position_type text NOT NULL,'\
#         'username text NOT NULL,'\
#         'FOREIGN KEY (position_id) REFERENCES orderbuffer (position_id) ON DELETE CASCADE'
#     ');')

# cursor.execute("INSERT INTO position_reference VALUES (-64757574,'NOVA','NIFTY','BUY','FINVANT');")

# query = 'select * from position_reference'
# cursor.execute(query)
# print(cursor.fetchall())


# query = 'DROP TABLE order_history'
# cursor.execute(query)
# print(cursor.fetchall())

# cursor.execute('CREATE TABLE IF NOT EXISTS order_history ('\
#     'order_id BIGINT NOT NULL,'\
#     'brokerage_id text NOT NULL,'\
#     'brokerage text NOT NULL,'\
#     'username text NOT NULL,'\
#     'strategy_name text NOT NULL,'\
#     'tradingsymbol text NOT NULL,'\
#     'position text NOT NULL,'\
#     'instrument_nomenclature text NOT NULL,'\
#     'order_status text NOT NULL,'\
#     'order_price real NOT NULL,'\
#     'order_qty integer NOT NULL,'\
#     'order_time text NOT NULL,'\
#     'PRIMARY KEY (order_id, order_time(255),instrument_nomenclature(255))'\
# ');')

# cursor.execute("INSERT INTO order_history VALUES (-617616127, 00, 'xx', 'NISARG','nova', 'NNN', 'BUY', 'CEPE' , 'placed', 1888, 10,'15:30');")

# query = 'select * from order_history'
# cursor.execute(query)
# print(cursor.fetchall())

db.commit()