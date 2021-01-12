import simple_modbus_server as sms

server = sms.Server(port=5020)
server.start()

server.set_coil(0, True)
