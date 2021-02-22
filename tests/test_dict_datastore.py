import time
import pytest
import modbus_server
from pyModbusTCP.client import ModbusClient


@pytest.fixture()
def modbus_server_instance():
    s = modbus_server.Server(port=5021, datastore=None, autostart=True)
    time.sleep(0.1)
    yield s
    s.stop()


@pytest.fixture()
def modbus_client():
    return ModbusClient(host="localhost", port=5021, auto_open=True)


def test_dict_read_coil(modbus_server_instance, modbus_client):
    modbus_server_instance.set_coil(0, True)
    assert modbus_client.read_coils(0, 1) == [True]


def test_dict_read_discrete_input(modbus_server_instance, modbus_client):
    modbus_server_instance.set_discrete_input(0, True)
    assert modbus_client.read_discrete_inputs(0, 1) == [True]


def test_dict_read_input_register(modbus_server_instance, modbus_client):
    modbus_server_instance.set_input_register(0, 1234, "h")
    assert modbus_client.read_input_registers(0, 1) == [1234]


def test_dict_read_holding_register(modbus_server_instance, modbus_client):
    modbus_server_instance.set_holding_register(0, 1234, "h")
    assert modbus_client.read_holding_registers(0, 1) == [1234]
