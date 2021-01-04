import redis


class RedisDatastore:
    def __init__(self, host="localhost", port=6379, db=0, initial_config={}):
        self.host = host
        self.port = port
        self.db = db
        self.initial_config = initial_config

    def __enter__(self):
        self.r = redis.Redis(host=self.host, port=self.port, db=self.db)
        return self.r

    def __exit__(self, type, value, traceback):
        self.r.close()


class DictDatastore:
    def __init__(self, initial_config={}):
        self.initial_config = initial_config
