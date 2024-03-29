import struct
import distutils.util
import warnings
import logging

logger = logging.getLogger("modbus_server_logger")

try:
    import redis
except ImportError:
    logging.info("Could not import redis, RedisDatastore is not available")

# 32 and 64 bit values work differently between the two datastores!


class DictDatastore:
    def __init__(self):
        self.empty_datadict = {
            "coils": {},
            "discrete_inputs": {},
            "input_registers": {},
            "holding_registers": {},
        }
        self.datadict = dict(self.empty_datadict)
        logger.debug("Initialized empty DictDatastore")

    def read(self, object_reference, first_address, number_of_records):
        data = []
        for address in range(first_address, first_address + number_of_records):
            data.append(self.datadict[object_reference][address])
        return data

    def write(self, object_reference, address, value, encoding):

        if object_reference in ("input_registers", "holding_registers"):
            if struct.calcsize(encoding) == 2:
                value = struct.pack(f"!{encoding}", value)
            elif struct.calcsize(encoding) > 2:
                number_of_registers = struct.calcsize(encoding) // 2
                value_as_bytes = struct.pack(f"!{encoding}", value)
                for chunk_number in range(0, number_of_registers):
                    byte_chunk = value_as_bytes[chunk_number * 2 : chunk_number * 2 + 2]
                    self.datadict[object_reference][address + chunk_number] = byte_chunk
                return

        self.datadict[object_reference][address] = value

    def dump(self):
        return self.datadict

    def empty(self):
        self.datadict = dict(self.empty_datadict)


class RedisDatastore:
    def __init__(
        self, modbus_address_map={}, redis_host="localhost", redis_port=6379, redis_db=0
    ):

        self.host = redis_host
        self.port = redis_port
        self.db = redis_db
        self.modbus_address_map = modbus_address_map
        self.r = None
        self._verify_modbus_address_map()
        self._connect()
        logger.debug("Initialized RedisDatastore")

    def _connect(self):
        self.r = redis.Redis(self.host, self.port, self.db)
        self.r.ping()  # Check the connection

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

    def apply_initial_values(self):
        for object_reference, addresses in self.modbus_address_map.items():
            for address, props in addresses.items():
                self.r.set(props["key"], props["initial_value"])

    def print_address_map(self):
        print(self.modbus_address_map)

    def print_all_current_values(self):
        for object_reference, address_map in self.modbus_address_map.items():
            print(object_reference)
            for address, props in address_map.items():
                print(
                    f"\tAddress: {address} -> {props['key']} : {self.r.get(props['key'])}"
                )

    def read(self, object_reference, first_address, number_of_records):
        data = []
        for address in range(first_address, first_address + number_of_records):
            address_properties = self.modbus_address_map[object_reference][str(address)]
            key = address_properties["key"]

            raw_value = self.r.get(key)

            if raw_value is None:
                logger.warning(
                    f"Key {key} for {object_reference}:{address} not found in redis"
                )
                raise KeyError(f"Key {key} could not be found in redis datastore")

            unicode_value = raw_value.decode()
            logger.debug(
                f"Getting {key} for {object_reference}:{address} from redis -> {unicode_value}"
            )

            if object_reference in ("coils", "discrete_inputs"):
                # Cast value from string to bool:
                value = bool(distutils.util.strtobool(unicode_value))

            elif object_reference in ("input_registers", "holding_registers"):
                encoding = address_properties["encoding"]

                if encoding in ("h", "H", "i", "I"):  # ints
                    value = struct.pack(f"!{encoding}", int(unicode_value))
                if encoding in ("e", "f", "d"):  # floats
                    value = struct.pack(f"!{encoding}", float(unicode_value))

                if encoding in ("i", "I", "f", "d"):
                    # >2 bytes: Find out which part is requested:
                    part = address_properties["part"]
                    value = value[(part - 1) * 2 : part * 2]

            data.append(value)

        return data

    def write(self, object_reference, address, value, encoding):

        if type(value) == bool:
            value = str(value)

        try:
            key = self.modbus_address_map[object_reference][str(address)]["key"]
        except KeyError:
            key = f"{object_reference}:{address}"
            self.modbus_address_map[object_reference][str(address)] = {
                "key": key,
                "encoding": encoding,
            }

        self.r.set(key, value)
