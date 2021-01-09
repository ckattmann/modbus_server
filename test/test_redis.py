import json
import simple_modbus_server as sms

with open("example_modbus_address_map.json") as f:
    modbus_address_map = json.load(f)

datastore = sms.RedisDatastore(modbus_address_map=modbus_address_map)

modbus_server = sms.Server(port=5020, datastore=datastore)

modbus_server.start()
