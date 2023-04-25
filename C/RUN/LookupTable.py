
# A function to check order_reference table (for instrument_token) and update the lookup table cntr
import json
import sqlite3
from time import sleep

def UpdateLookup_table():
    print('Updating Lookup Table...')

    # Open connection
    conn = sqlite3.connect('../Data/OrderData.db')
    c = conn.cursor()

    # Get a list of all instrument_tokens in order_reference table and their corresponding cntr
    c.execute("SELECT instrument_token FROM order_reference")
    instrument_tokens = c.fetchall()
    # print(instrument_tokens)

    # Traverse the list and update the lookup table
    instrument_token_data = {}
    for instrument_token in instrument_tokens:
        if str(instrument_token[0]) in instrument_token_data:
            instrument_token_data[str(instrument_token[0])] += 1
        else:
            instrument_token_data[str(instrument_token[0])] = 1


    # Write to lookup table
    with open('../Data/Lookup_Table.json', 'w') as f:
        json.dump(instrument_token_data, f, indent=4)

    # Close connection + commit
    conn.commit()
    conn.close()

def run():
    while True:
        UpdateLookup_table()
        sleep(5)

if __name__ == '__main__':
    run()