import importlib.util
import json
import redis


class DictDatastore:
    def __init__(self):
        self.datastore = {
            "coils": {},
            "discrete_inputs": {},
            "input_registers": {},
            "holding_registers": {},
        }
        # self.register_encodings = {
        #     "input_registers": {},
        #     "holding_registers": {},
        # }

    def read(self, object_reference, first_address, quantity_of_records):
        data = []
        for address in range(first_address, first_address + quantity_of_records):
            data.append(self.datastore[object_reference][address])
        return data

    def write(self, object_reference, address, value):
        self.datastore[object_reference][address] = value

    def dump(self):
        return self.datastore


class RedisDatastore:
    def __init__(self, host="localhost", port=6379, db=0, modbus_address_map):
        if importlib.util.find_spec("redis") is not None:
            import redis
        else:
            raise ImportError(
                "RedisDatastore requires redis-py (https://github.com/andymccurdy/redis-py),\
                which you can install with 'pip install redis'"
            )
        self.host = host
        self.port = port
        self.db = db
        self.modbus_address_map = modbus_address_map
        self.r = None
        self._connect()

    def _connect(self):
        self.r = redis.Redis(self.host, self.port, self.db)

    def read(self, object_reference, first_address, quantity_of_records):
        data = []
        for address in range(first_address, first_address + quantity_of_records):
            key = self.modbus_address_map[object_reference][address]["key"]
            data.append(r.get(key))
        return data
