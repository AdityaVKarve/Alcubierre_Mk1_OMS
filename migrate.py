import sqlite3
import pymysql

#connect to AWS database
db = pymysql.connect(host="database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com", user="admin", password="FinvantResearch")
cursor = db.cursor()
cursor.execute('use test')

#connect to local database 
conn = sqlite3.connect('C/Data/OrderData.db')
cur = conn.cursor()

#select the table you want to use
query = 'SELECT * FROM order_history'
cur.execute(query)

# Fetch all rows from the table
rows = cur.fetchall()

# Process the fetched data
#For every row in the table of our local database we will insert all the column values to our AWS database.
for row in rows:

    #row_data contains all the column values for single row 
    row_data = []
    for i in range(len(row)):
        row_data.append(row[i])
    # print(row_data)
    
    #for dynamically putting all the places for our column values to be inserted in those places
    placeholders = ','.join(['%s'] * len(row_data))
    query = f'INSERT INTO order_history VALUES ({placeholders})'
    
    #executing query with query and paramaters
    cursor.execute(query, tuple(row_data))
    

conn.commit()
db.commit()

#close the connection 
cursor.close()
db.close()
