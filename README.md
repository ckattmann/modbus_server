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
### Server Object
`s = modbus_server.Server(host='localhost', port=502, datastore=None, loglevel="INFO", autostart=False)`

Initializes a Server instance. If the `datastore` is not explicitly given, an empty `DictDatastore` is instantiated and used.

`s.start()`

`s.stop()`

Start and stop the server thread which accepts requests. The thread does not block the main thread, but it prevents the program from exiting until s.stop() is called.

### Set Coils and Discrete Input
`set_coil(address, value)`

`set_discrete_input(address, value)`

Set the coil or discrete_input at _address_ to _value_. This function can only process one value.

`set_coils(start_address, values)`

`set_discrete_inputs(start_address, values)`

### Set Input and Holding Registers
`set_input_register(address, value, encoding)`

`set_holding_register(address, value, encoding)`

Set the input or holding register at _address_ to _value_ using _encoding_. This function can only process one value.

`set_input_registers(start_address, values, encoding)`

`set_holding_registers(start_address, values, encoding)`

### Datastore Object
The modbus_server pulls the data it serves from a _datastore_. The simplest datastore is just a dictionary that is filled from the Server object using the various `set_`-functions described below. In that case, the data needs to be ingested directly in the program that starts the server as in the minimal example above.

`datastore = modbus_server.DictDatastore()`

An alternative is using redis to hold the data. That way, other processes in the system can change the data in the datastore and the modbus_server always has up to data from e.g. a measurement process. In order to link keys in redis with modbus object references (coil, discrete input, input register, and holding register) and addresses, the RedisDatastore object uses a `modbus_address_map`, a dictionary that follows a special convention.

`datastore = modbus_server.RedisDatastore(modbus_address_map={}, redis_host="localhost", redis_port=6379, redis_db=0)`

## Development:
For testing, install a symlink to the package in the python environment using flit:
```shell
flit install . -s
```
