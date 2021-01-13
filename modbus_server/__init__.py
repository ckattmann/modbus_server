""" Easy-to-use ModbusTCP Server in pure Python """

__version__ = "0.1.0"

from .modbus_server import Server

from .modbus_datastore import DictDatastore, RedisDatastore
