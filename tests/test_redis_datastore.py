import json
import pytest


# r.set("example_input_register_0", 1234)
# r.set("example_holding_register_0", 4321)


@pytest.fixture(autouse=True)
def redis_client():
    import redis

    r = redis.Redis(host="localhost", port=6379, db=0)
    r.ping()
    return r


@pytest.fixture(autouse=True)
def modbus_server_instance():
    import modbus_server

    with open("tests/example_modbus_address_map.json") as f:
        modbus_address_map = json.load(f)

    datastore = modbus_server.RedisDatastore(modbus_address_map)
    s = modbus_server.Server(port=5020, datastore=datastore, autostart=True)
    yield s
    s.stop()


@pytest.fixture(autouse=True)
def modbus_client():
    from pyModbusTCP.client import ModbusClient

    return ModbusClient(host="localhost", port=5020, auto_open=True)


def test_redis_read_coil(redis_client, modbus_client):
    redis_client.set("example_coil_0", 1)
    assert modbus_client.read_coils(0, 1) == [True]


def test_redis_read_discrete_input(redis_client, modbus_client):
    redis_client.set("example_discrete_input_0", 1)
    assert modbus_client.read_discrete_inputs(0, 1) == [True]


def test_redis_read_input_register(redis_client, modbus_client):
    redis_client.set("example_input_register_0", 1234)
    assert modbus_client.read_input_registers(0, 1) == [1234]


def test_redis_read_holding_register(redis_client, modbus_client):
    redis_client.set("example_holding_register_0", 1234)
    assert modbus_client.read_holding_registers(0, 1) == [1234]
