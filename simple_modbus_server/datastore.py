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


# class RedisDatastore:
#     def __init__(self, host="localhost", port=6379, db=0):
#         self.host = host
#         self.port = port
#         self.db = db

#     def _connect(self):
#         redis
