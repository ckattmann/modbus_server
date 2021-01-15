import struct
import distutils.util
import json
import warnings
import logging

try:
    import redis
except ImportError:
    logging.info("Could not import redis, RedisDatastore is not available")


class DictDatastore:
    def __init__(self):
        self.datadict = {
            "coils": {},
            "discrete_inputs": {},
            "input_registers": {},
            "holding_registers": {},
        }
        logging.debug("Initialized empty DictDatastore")

    def read(self, object_reference, first_address, quantity_of_records):
        data = []
        for address in range(first_address, first_address + quantity_of_records):
            data.append(self.datadict[object_reference][address])
        return data

    def write(self, object_reference, address, value, encoding):

        if object_reference in ("input_registers", "holding_registers"):
            if struct.calcsize(encoding) == 2:
                value = struct.pack(f"!{encoding}", value)
            elif struct.calcsize(encoding) > 2:
                number_of_registers = struct.calcsize(encoding) // 2
                value_bytes = struct.pack(f"!{encoding}", value)
                for chunk_number in range(0, number_of_registers):
                    byte_chunk = value_bytes[chunk_number * 2, chunk_number * 2 + 2]
                    self.datadict[object_reference][address + chunk_number] = value
                return

        self.datadict[object_reference][address] = value

    def dump(self):
        return self.datadict


class RedisDatastore:
    def __init__(self, host="localhost", port=6379, db=0, modbus_address_map={}):

        self.host = host
        self.port = port
        self.db = db
        self.modbus_address_map = modbus_address_map
        self.r = None
        self._verify_modbus_address_map()
        self._connect()
        logging.debug("Initialized RedisDatastore")

    def _connect(self):
        self.r = redis.Redis(self.host, self.port, self.db)

    def _verify_modbus_address_map(self):
        for key in self.modbus_address_map.keys():
            if key not in (
                "coils",
                "discrete_inputs",
                "input_registers",
                "holding_registers",
            ):
                warnings.warn(f"modbus_address_map contains non-standard key {key}")
        for std_key in (
            "coils",
            "discrete_inputs",
            "input_registers",
            "holding_registers",
        ):
            if std_key not in self.modbus_address_map:
                self.modbus_address_map[std_key] = {}

    # def set_initial_values(self):
    # TODO:
    #     self.modbus_address_map

    def read(self, object_reference, first_address, quantity_of_records):
        data = []
        for address in range(first_address, first_address + quantity_of_records):
            key = self.modbus_address_map[object_reference][address]["key"]
            logging.debug(f"Getting {key} for {object_reference}:{key} from redis")
            raw_value = self.r.get(key)

            if object_reference in ("input_registers", "holding_registers"):
                encoding = self.modbus_address_map[object_reference][address]["encoding"]

                if encoding in ("h", "H", "i"):  # ints
                    cast = int
                if encoding in ("e", "f", "d"):  # floats
                    cast = float
                value = struct.pack(f"!{encoding}", cast(raw_value))

                if encoding in ("i", "I", "f", "d"):
                    # >2 bytes: Find out which part is requested:
                    part = self.modbus_address_map[object_reference][address]["part"]
                    value_bytes = struct.pack(f"!{encoding}", value)
                    value = value_bytes[part * 2 : part * 2 + 2]

            elif object_reference in ("coils", "discrete_inputs"):
                # Cast value from string to bool:
                value = bool(distutils.util.strtobool(raw_value.decode()))

            data.append(value)

        return data

    def write(self, object_reference, address, value, encoding):
        if type(value) == bool:
            value = str(value)
        try:
            key = self.modbus_address_map[object_reference][address]["key"]
        except KeyError:
            key = f"{object_reference}:{address}"
            self.modbus_address_map[object_reference][address] = {
                "key": key,
                "encoding": encoding,
            }
        self.r.set(key, value)
