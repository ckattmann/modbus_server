import simple_modbus_server as sms

server = sms.Server(host="localhost", port=5020)

server.set_value(object_reference=3, address=1, value=19)

server.start()
print("Started Modbus Server...")
