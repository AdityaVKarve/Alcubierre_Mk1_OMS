import pymysql
db = pymysql.connect(host="database-1.cc8twgnxgsjl.ap-south-1.rds.amazonaws.com",user="admin",password="FinvantResearch" ,db="test")
cursor = db.cursor()

# cursor.execute('DELETE FROM order_history')
# cursor.execute('DELETE FROM orderbook')
# cursor.execute('DELETE FROM order_reference')
# cursor.execute('DELETE FROM orderbuffer')
# cursor.execute('DELETE FROM position_reference')
# for row in rows:
#     print(row)

# cursor.execute('DELETE FROM orderbook WHERE order_status="PLACED" ')
# cursor.execute('DELETE FROM orderbuffer WHERE username="fin_user_1" ')

print('orderbook table :')
query = 'select * from orderbook'
cursor.execute(query)
# print(cursor.fetchall())
rows = cursor.fetchall()

for row in rows:
    print(row)


print('\n')
print('order_reference table :')
query = 'select * from order_reference'
cursor.execute(query)
# print(cursor.fetchall())
rows = cursor.fetchall()

for row in rows:
    print(row)



print('\n')
print('orderbuffer table :')
query = 'select * from orderbuffer'
cursor.execute(query)
# print(cursor.fetchall())
rows = cursor.fetchall()

for row in rows:
    print(row)


print('\n')
print('position_preference table :')
query = 'select * from position_reference'
cursor.execute(query)
# print(cursor.fetchall())
rows = cursor.fetchall()

for row in rows:
    print(row)

print('\n')

print('order_history table :')
query = 'select * from order_history'
cursor.execute(query)
rows = cursor.fetchall()
for row in rows:
    print(row)

print("Number of rows in order_history : " + str(len(rows)))

db.commit()