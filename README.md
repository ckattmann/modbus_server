# modbus_server
A ModbusTCP server implementation in pure Python.

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
- Test 32bit values
- Test performance

## Development:
For testing, install a symlink to the package in the python environment using flit:
```shell
flit install . -s
```
