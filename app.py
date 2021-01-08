import simple_modbus_server as sms

server = sms.Server(host="localhost", port=5020)

server.set_value(object_reference=3, address=1, value=19)

server.start()
print("Started Modbus Server...")

# With Redis Datastore:
# =====================

with open("modbus_address_map") as f:
    modbus_address_map = json.load(f)

datastore = SimpleModbusServer.RedisDatastore(
    host="localhost", port=6379, db=0, modbus_address_map=modbus_address_map
)
sms.Server(host="localhost", port=5020, datastore=datastore)


# For Registers:
# ==============
# Encoding can be h (short), H (unsigned short), e (float16)
server.set_input_register(0, 1.5, encoding="e")
