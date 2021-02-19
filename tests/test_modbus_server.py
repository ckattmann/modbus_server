import time
import random

import chalk
from icecream import ic

from pymodbus.client.sync import ModbusTcpClient

# from .. import modbus_server
import modbus_server

PORT = random.randint(2000, 10000)

# Helper Function to print yellow with yellow()
yellow = lambda s: print(chalk.yellow(s))


class pymodbus_client:
    def __init__(self, host="127.0.0.1", port=PORT):
        self.client = ModbusTcpClient(host=host, port=port)

    def __enter__(self):
        return self.client

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()


# def test_illegal_function():
#     with pymodbus_client() as client:
#         result = client.write_coil(address=0, value=True)
#         # pprint(dir(result))
#         print(result.fcode)
#         print(result.message)
#         assert result.isError() == True


def assert_bits(obj_ref, address, count=1, expect_result=True, expect_error=False):
    with pymodbus_client() as client:
        if obj_ref == "coils":
            result = client.read_coils(address=address, count=count)
        elif obj_ref == "discrete_inputs":
            result = client.read_discrete_inputs(address=address, count=count)
        else:
            raise ValueError()
        assert result.isError() == expect_error
        if not expect_error:
            if type(expect_result) == bool:
                assert result.bits[:count] == [expect_result] * count
            elif type(expect_result) in (list, tuple):
                assert result.bits == expect_result


def assert_registers(obj_ref, address, count=1, expect_result=0, expect_error=False):
    with pymodbus_client() as client:
        if obj_ref == "input_registers":
            result = client.read_input_registers(address=address, count=count)
        elif obj_ref == "holding_registers":
            result = client.read_holding_registers(address=address, count=count)
        else:
            raise ValueError()
        assert result.isError() == expect_error
        if not expect_error:
            ic(result.registers)
            if type(expect_result) in (int, float):
                assert result.registers[:count] == [expect_result] * count
            elif type(expect_result) in (list, tuple):
                assert result.registers == expect_result


def check_bits(s, obj_ref):

    s.set_coil(0, True)
    s.set_coil(1, False)
    s.set_coils(10000, values=[True] * 200)

    s.set_discrete_input(0, True)
    s.set_discrete_input(1, False)
    s.set_discrete_inputs(10000, values=[True] * 200)

    # Read Addresses 0 and 1:
    assert_bits(obj_ref, address=0, expect_result=True)
    assert_bits(obj_ref, address=1, expect_result=False)

    # Read Addresses 10000 - 10200:
    assert_bits(obj_ref, address=10000, count=200)

    # Expect Exception 2 - Illegal Data Address:
    assert_bits(obj_ref, address=0, count=3, expect_error=True)
    assert_bits(obj_ref, address=3, count=1, expect_error=True)

    # Expect Exception 3 - Illegal Data Value:
    assert_bits(obj_ref, address=0, count=0, expect_error=True)
    assert_bits(obj_ref, address=0, count=2000, expect_error=True)


def check_registers(s, obj_ref):

    s.set_input_register(0, 13, encoding="h")
    s.set_input_register(1, 14, encoding="h")
    s.set_input_registers(10000, values=[1000, 1001, 1002], encoding="H")

    s.set_holding_register(0, 15, encoding="h")
    s.set_holding_register(1, 16, encoding="h")
    s.set_holding_registers(10000, values=[1000, 1001, 1002], encoding="H")

    # Read Addresses 0 and 1:
    assert_registers(obj_ref, address=0, expect_result=True)
    assert_registers(obj_ref, address=1, expect_result=False)

    # Read Addresses 10000 - 10200:
    assert_registers(obj_ref, address=10000, count=3, expect_result=[1000, 1001, 1002])

    # Expect Exception 2 - Illegal Data Address:
    assert_registers(obj_ref, address=0, count=3, expect_error=True)
    assert_registers(obj_ref, address=3, count=1, expect_error=True)

    # Expect Exception 3 - Illegal Data Value:
    assert_registers(obj_ref, address=0, count=0, expect_error=True)
    assert_registers(obj_ref, address=0, count=126, expect_error=True)


def test_bits_with_DictDatastore():
    s = modbus_server.Server(host="localhost", port=PORT, daemon=True)
    s.start()
    time.sleep(0.5)

    check_bits(s, "coils")
    check_bits(s, "discrete_inputs")

    s.stop()


def test_bits_with_RedisDatastore():
    datastore = modbus_server.RedisDatastore()
    s = modbus_server.Server(
        host="localhost", port=PORT, daemon=True, datastore=datastore
    )
    s.start()
    time.sleep(0.5)

    check_bits(s, "coils")
    check_bits(s, "discrete_inputs")

    s.stop()


def test_registers_with_DictDatastore():
    s = modbus_server.Server(host="localhost", port=PORT, daemon=True)
    s.start()
    time.sleep(0.5)

    check_registers(s, "input_registers")
    check_registers(s, "holding_registers")

    s.stop()


def test_registers_with_RedisDatastore():
    datastore = modbus_server.RedisDatastore()
    s = modbus_server.Server(
        host="localhost", port=PORT, daemon=True, datastore=datastore
    )
    s.start()
    time.sleep(0.5)

    check_registers(s, "input_registers")
    check_registers(s, "holding_registers")

    s.stop()


def notest_RedisDatastore_with_json():
    with open("example_modbus_address_map.json") as f:
        modbus_address_map = json.load(f)
    datastore = modbus_server.RedisDatastore(modbus_address_map)
    s = modbus_server.Server(
        host="localhost", port=PORT, daemon=True, datastore=datastore
    )
    s.start()
    time.sleep(0.5)

    # r = redis.Redis
    s.stop()
