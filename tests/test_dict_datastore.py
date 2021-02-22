import pytest


@pytest.fixture(autouse=True)
def modbus_server_instance():
    import modbus_server

    s = modbus_server.Server(port=5021, datastore=None, autostart=True, daemon=True)
    s.datastore.empty()
    yield s
    s.stop()


@pytest.fixture(autouse=True)
def modbus_client():
    from pyModbusTCP.client import ModbusClient

    return ModbusClient(host="localhost", port=5021, auto_open=True)


def test_dict_read_coil(modbus_server_instance, modbus_client):
    print(modbus_server_instance)
    modbus_server_instance.set_coil(0, True)
    print(modbus_server_instance.datastore.dump())
    assert modbus_client.read_coils(0, 1) == [True]


# def test_dict_read_discrete_input(modbus_server_instance, modbus_client):
#     modbus_server_instance.set("example_discrete_input_0", 1)
#     assert modbus_client.read_discrete_inputs(0, 1) == [True]


# def test_dict_read_input_register(modbus_server_instance, modbus_client):
#     modbus_server_instance.set("example_input_register_0", 1234)
#     assert modbus_client.read_input_registers(0, 1) == [1234]


# def test_dict_read_holding_register(modbus_server_instance, modbus_client):
#     redis_client.set("example_holding_register_0", 1234)
#     assert modbus_client.read_holding_registers(0, 1) == [1234]
