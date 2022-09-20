import json
import modbus_server

with open("example_modbus_address_map.json") as f:
    am = json.load(f)
print(am)

print(modbus_server.__file__)
print(modbus_server.__version__)

datastore = modbus_server.RedisDatastore(modbus_address_map=am)
datastore.apply_initial_values()
s = modbus_server.Server(port=2222, datastore=datastore)

s.start()
