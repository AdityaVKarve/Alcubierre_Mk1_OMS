import json

with open('../Config/DATASERVER.json') as f:
    config = json.load(f)

SECTION = config['SECTION'] 
