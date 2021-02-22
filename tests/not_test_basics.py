import modbus_server

s = modbus_server.Server(
    host="localhost", port=5020, daemon=True, loglevel="WARNING", autostart=False
)

s.start()

s.set_coil(1, True)
s.set_coils(2, [True, False, True])

s.set_discrete_input(1, True)
s.set_discrete_inputs(2, [True, False, True])

s.set_input_register(1, 1234, "h")
s.set_input_registers(2, [1, 2, 3, 4, 5], "h")

s.set_holding_register(1, 1234, "h")
s.set_holding_registers(2, [1, 2, 3, 4, 5], "h")

s.stop()
