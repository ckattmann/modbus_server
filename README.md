# modbus_server
A Modbus server implementation in pure Python.

## Installation
```shell
pip install modbus_server
```

## Usage
```python
import modbus_server
s = modbus_server.Server(port=5020)
s.start()
s.set_coil(1,True)
```

## Todo:
- Client tests with pyModbusTCP
- Test 32bit values
- Test performance

## Testing:
For testing, install a symlink to the package in the python environment using flit:
```shell
flit install . -s
```
