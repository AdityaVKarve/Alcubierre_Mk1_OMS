'''
username: admin
password: FinvantResearch
port: 3306
endpoint: database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com
'''

import pymysql

db = pymysql.connect(host="database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com",user="admin",password="FinvantResearch")
cursor = db.cursor()
cursor.execute("select version()")
cursor.execute("use test") # This connects to the database named test
# query = 'CREATE DATABASE IF NOT EXISTS orderbook'
# cursor.execute(query)

# print(cursor.fetchall())
# query = "CREATE TABLE IF NOT EXISTS orderbook (id INT AUTO_INCREMENT PRIMARY KEY, tradingsymbol VARCHAR(255), exchange_token VARCHAR(255), lot_size INT, total_qty INT, placed_qty INT, instrument_token INT)"
# cursor.execute(query)
# print(cursor.fetchall())

# query = "INSERT INTO orderbook (tradingsymbol, exchange_token, lot_size, total_qty, placed_qty, instrument_token) VALUES ('NIFTY21JUNFUT', 'NFO', 75, 75, 1, 0)"
# cursor.execute(query)
# print(cursor.fetchall())


# query = 'select * from orderbook'
# cursor.execute(query)
# print(cursor.fetchall())

# query = 'DROP TABLE orderbook'
# cursor.execute(query)
# print(cursor.fetchall()

# show all tables
query = 'show tables'
cursor.execute(query)
print(cursor.fetchall())

# show description of aLL tables
query = 'select * from order_history'
cursor.execute(query)
res = cursor.fetchall()
for r in res:
    print(r)

# commit the changes
db.commit()


## table -> orderbook -> enter a row -> fetch that