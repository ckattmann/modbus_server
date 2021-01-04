from icecream import ic
from pymodbus.client.sync import ModbusTcpClient

# client.write_coil(1, True)
# result = client.read_coils(1, 1)


class pymodbus_client:
    def __init__(self, host="127.0.0.1", port=5020):
        self.client = ModbusTcpClient(host=host, port=port)

    def __enter__(self):
        return self.client

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.client.close()


def test_read_input_register():
    """Read Input register 1
    Expected Result: 19 (must be prefilled)
    """
    with pymodbus_client() as client:
        result = client.read_input_registers(1, 1)
    assert result.isError() == False
    assert result.registers[0] == 19


def test_read_coil():
    """Read coil 1
    Expected Result: True (must be prefilled)
    """
    with pymodbus_client() as client:
        result = client.read_coil(1, 1)
    assert result.isError() == False
    assert result.registers[0] == True


if __name__ == "__main__":
    import pprint
    import inspect

    test_functions = [k for k, v in globals().items() if inspect.isfunction(v)]

    for func in test_functions:
        globals()[func]()
