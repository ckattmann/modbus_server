import time

import chalk
from icecream import ic

from pymodbus.client.sync import ModbusTcpClient

import simple_modbus_server as sms

# client.write_coil(1, True)
# result = client.read_coils(1, 1)


class pymodbus_client:
    def __init__(self, host="127.0.0.1", port=5020):
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


def test_read_coils():

    s = sms.Server(host="localhost", port=5020)
    s.start()
    time.sleep(0.5)

    s.set_coil(0, True)
    s.set_coil(1, False)

    # Read Addresses 0 and 1:
    with pymodbus_client() as client:
        result = client.read_coils(address=0, count=2)
        assert result.isError() == False
        assert result.bits[0] == True
        assert result.bits[1] == False
        print(result.bits[2:8])
        assert result.bits[2:8] == [False] * 6

    # Read Addresses 10000 - 10200:
    s.set_coils(10000, values=[True] * 200)
    with pymodbus_client() as client:
        result = client.read_coils(address=10000, count=200)
        assert result.isError() == False
        assert result.bits == [True] * 200

    # Exception 2 - Illegal Data Address
    with pymodbus_client() as client:
        result = client.read_coils(address=0, count=3)
        assert result.isError() == True

    with pymodbus_client() as client:
        result = client.read_coils(address=3, count=1)
        assert result.isError() == True

    # Exception 3 - Illegal Data Value
    with pymodbus_client() as client:
        result = client.read_coils(address=0, count=0)
        assert result.isError() == True

    with pymodbus_client() as client:
        result = client.read_coils(address=0, count=2000)
        assert result.isError() == True

    s.stop()


def test_discrete_inputs():
    s = sms.Server(host="localhost", port=5020)
    s.start()
    time.sleep(0.5)

    s.set_discrete_input(0, value=False)
    s.set_discrete_input(1, value=True)

    print(chalk.yellow("Request address normally:"))
    with pymodbus_client() as client:
        result = client.read_discrete_inputs(address=0, count=2)
        assert result.isError() == False
        assert result.bits[0] == False
        assert result.bits[1] == True
        print(result.bits[2:8])
        assert result.bits[2:8] == [False] * 6

    s.set_discrete_inputs(10000, values=[True] * 200)
    with pymodbus_client() as client:
        result = client.read_discrete_inputs(address=10000, count=200)
        assert result.isError() == False
        assert result.bits == [True] * 200

    # Exception 2 - Illegal Data Address
    print(chalk.yellow("Request address that is not set:"))
    with pymodbus_client() as client:
        result = client.read_discrete_inputs(address=0, count=3)
        assert result.isError() == True

    s.stop()


def now_test_read_input_registers():

    ## Test FC 3
    ## =========

    s.set_input_register(0, value=14, encoding="h")
    s.set_input_register(1, value=15, encoding="h")

    print(chalk.yellow("Request address normally:"))
    with pymodbus_client() as client:
        result = client.read_input_registers(address=0, count=2)
        assert result.isError() == False
        print(dir(result))
        print(result.registers)
        assert registers[0] == 14
        assert registers[0] == 15

    # s.set_discrete_inputs(10000, values=[True] * 200)
    # with pymodbus_client() as client:
    #     result = client.read_discrete_inputs(address=10000, count=200)
    #     assert result.isError() == False
    #     assert result.bits == [True] * 200

    # Exception 2 - Illegal Data Address
    print(chalk.yellow("Request address that is not set:"))
    with pymodbus_client() as client:
        result = client.read_input_registers(address=0, count=3)
        assert result.isError() == True


if __name__ == "__main__":
    from pprint import pprint
    import inspect

    # test_functions = [k for k, v in globals().items() if inspect.isfunction(v)]

    # for func in test_functions:
    #     globals()[func]()

    # Init Modbus Server:
    s = sms.Server(host="localhost", port=5020)
    s.start()
    time.sleep(0.5)

    now_test_read_input_registers()

    s.stop()
