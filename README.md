# modbus_server
A ModbusTCP server implementation in pure Python.

## Installation
```shell
pip install modbus_server
```

## Minimal Example
```python
import modbus_server
s = modbus_server.Server(port=5020)
s.start()
s.set_coil(1,True)
```

## Functions
`Server(host, port)`

Initializes a Server instance.

`set_coil(address, value)`

Set the coil at _address_ to _value_. This function can only process one value.

`set_coils(start_address, values)`


## Todo:
- Test 32bit values
- Test performance

## Development:
For testing, install a symlink to the package in the python environment using flit:
```shell
flit install . -s
```
