import time
import modbus_server
from pyModbusTCP.client import ModbusClient

print("test")
s = modbus_server.Server(port=5020)
s.start()
s.set_coil(1, True)
s.set_coil(2, True)
time.sleep(1)
# print(s.dump_datastore())

c = ModbusClient(host="localhost", port=5020)

res = c.read_coils(1, 1)
print(res)
res = c.read_coils(1, 1)
print(res)
res = c.read_coils(1, 1)
print(res)
