import socket
import struct
import threading
import logging

from . import modbus_datastore

# Constants:

FUNCTION_CODE_MAP = {
    1: "coils",
    2: "discrete_inputs",
    4: "input_registers",
    3: "holding_registers",
}


logger = logging.getLogger("modbus_server_logger")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(levelname)-10s: %(message)s")
streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)
logger.propagate = False  # prevent double logging


def pack_bools_to_bytes(bool_list):
    chars = []
    for j in range(0, len(bool_list), 8):
        bool_chunk = bool_list[j : j + 8]
        equivalent_char = 0
        for i, b in enumerate(bool_chunk):
            if b:
                equivalent_char += 2 ** i
        chars.append(equivalent_char)

    return struct.pack(f"!{len(chars)}B", *chars)


def build_error_response(header_items, exception_code):
    response_items = list(header_items)

    # Error Response Function Code -> Function Code + 128
    response_items[4] = header_items[4] + 128

    # In an error message, the data contains the Exception Code
    response_items.append(exception_code)

    return struct.pack(f"!HHHBBB", *response_items)


def handle_requests(s, addr, datastore):

    while True:

        # Recv max 255 bytes, the maximal length for a Modbus frame:
        data = s.recv(256)
        if not data:
            break
        if len(data) < 12:
            logger.error(
                f'Received less than 12 bytes, Header: {struct.unpack("!HHHBB", data[:8])}'
            )
            s.close()
            break

        ## Extract Header + Function Code:
        # Transaction ID:   (2 Bytes)   Identifies the request-response-pair, is echoed in the response
        # Protocol:         (2 Bytes)   Always 0 ("reserved for future use", lol)
        # Length:           (2 Bytes)   Length of the remaining frame in bytes (Total Length - 6)
        # Unit ID:          (1 Byte)    "Slave ID", inner identifier to route to different units (typically 0)
        # Function Code:    (1 Byte)    1,2,3,4,5,6,15,16,43: Read/Write input/register etc.
        try:
            (
                transaction_id,
                protocol,
                length,
                unit_id,
                function_code,
            ) = struct.unpack("!HHHBB", data[:8])
        except struct.error:
            logger.error(f"Received incompatible header bytes {data}")
            continue

        # Pack header items into a tuple which can more easily be passed around:
        header_items = (transaction_id, protocol, length, unit_id, function_code)

        # Check if Function Code is valid:
        if function_code not in (1, 2, 3, 4):
            # Respond with exception 01 - Illegal Function:
            response = build_error_response(header_items, exception_code=1)
            s.sendall(response)
            continue

        if function_code in (1, 2, 3, 4):  # -> The 4 'Read' Function Codes
            first_address = struct.unpack("!H", data[8:10])[0]
            number_of_registers = struct.unpack("!H", data[10:12])[0]

        object_reference = FUNCTION_CODE_MAP[function_code]

        ## Validate number of objects requested and respond with exception 3 if invalid:
        ## =============================================================================

        if object_reference in ("coils", "discrete_inputs"):
            if number_of_registers < 1 or number_of_registers > 2000:
                response = build_error_response(header_items, exception_code=3)
                s.sendall(response)
                continue

        if object_reference in ("input_registers", "holding_registers"):
            if number_of_registers < 1 or number_of_registers > 125:
                s.sendall(build_error_response(header_items, exception_code=3))
                continue

        ## Read addresses from datastore
        ## =============================

        try:
            data = datastore.read(object_reference, first_address, number_of_registers)
        except KeyError:
            # Address not in datastore -> Respond with exception 02 - Illegal Data Address:
            logger.warning(
                f"Request from {addr[0]} for {object_reference}:{first_address} -> Modbus Error 2: Illegal Data Address"
            )
            response = build_error_response(header_items, exception_code=2)
            s.sendall(response)
            continue
        except Exception as e:
            # Other Error -> Respond with exception 04 - Slave Device Failure:
            logger.error(
                f"Request from {addr[0]} for {object_reference}:{first_address} -> Modbus Error 4: Slave Device Failure"
            )
            # This is probably a bug in datastore.read(), so raise:
            raise
            response = build_error_response(header_items, exception_code=4)
            s.sendall(response)
            continue

        ## Compose response
        ## ================

        if object_reference in ("coils", "discrete_inputs"):
            data_bytes = pack_bools_to_bytes(data)

        if object_reference in ("input_registers", "holding_registers"):
            data_bytes = b"".join(data)

        # Response length is 3 fixed bytes (unit_id, function_code, number_of_data_bytes) plus the data bytes:
        response_message_length = 3 + len(data_bytes)
        number_of_data_bytes = len(data_bytes)

        # Compose response header:
        response_header_items = [
            transaction_id,
            protocol,
            response_message_length,
            unit_id,
            function_code,
            number_of_data_bytes,
        ]

        logger.debug(
            f"Request from {addr[0]} for {object_reference}:{first_address}+{number_of_registers} -> Response {data_bytes}"
        )

        # Pack response items into binary format and append data_bytes:
        response = struct.pack(f"!HHHBBB", *response_header_items) + data_bytes
        s.sendall(response)


class Server:
    def __init__(
        self,
        host="localhost",
        port=502,
        datastore=None,
        loglevel="INFO",
        autostart=False,
    ):
        streamhandler.setLevel(loglevel)
        self.host = host
        self.port = port
        if datastore is None:
            self.datastore = modbus_datastore.DictDatastore()
        else:
            self.datastore = datastore
        self.server_thread = None
        self.stop_server = False
        if autostart:
            self.start()

    def start(self):
        self.server_thread = threading.Thread(target=self._start_accepting)
        # self.server_thread.daemon = True
        self.server_thread.start()
        logger.info(f"Modbus Server started on port {self.port}")

    def _start_accepting(self):
        while not self.stop_server:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((self.host, self.port))
                s.listen(20)
                con, addr = s.accept()
                # logger.debug(f"Connected to {addr[0]} on port {addr[1]}")
                handling_thread = threading.Thread(
                    target=handle_requests, args=(con, addr, self.datastore)
                )
                handling_thread.daemon = True
                handling_thread.start()

    def stop(self):
        self.stop_server = True
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect((self.host, self.port))
            except ConnectionRefusedError:
                pass
        if self.server_thread:
            self.server_thread.join(timeout=2)
            self.server_thread = None
        logger.info("Modbus Server stopped")

    def dump_datastore(self):
        return self.datastore.dump()

    ## Convenience Functions for direct access to object reference (single + multiple):
    ## ================================================================================

    def set_coil(self, address, value):
        self._set_value("coils", address, value)

    def set_coils(self, start_address, values):
        address = start_address
        for value in values:
            self._set_value("coils", address, value)
            address += 1

    def set_discrete_input(self, address, value):
        self._set_value("discrete_inputs", address, value)

    def set_discrete_inputs(self, start_address, values):
        address = start_address
        for value in values:
            self._set_value("discrete_inputs", address, value)
            address += 1

    def set_input_register(self, address, value, encoding):
        self._set_value("input_registers", address, value, encoding)

    def set_input_registers(self, start_address, values, encoding):
        address = start_address
        for value in values:
            self._set_value("input_registers", address, value, encoding)
            address += struct.calcsize(encoding) // 2

    def set_holding_register(self, address, value, encoding):
        self._set_value("holding_registers", address, value, encoding)

    def set_holding_registers(self, start_address, values, encoding):
        address = start_address
        for value in values:
            self._set_value("holding_registers", address, value, encoding)
            address += struct.calcsize(encoding) // 2

    # Actually set the value:
    # =======================

    def _set_value(self, object_reference, address, value, encoding=None):

        # Verify address:
        if type(address) is not int:
            raise TypeError(f"type of 'address' must be int, not {type(address)}")
        if address < 0 or address > 65535:
            raise ValueError(f"'address' must be between 0 and 65535, not {address}")

        # Verify if value is boolean for coils and discrete inputs:
        # This is not done with bool(), because bool('0') == True might be confusing
        if object_reference in ("coils", "discrete_inputs") and not type(value) == bool:
            raise TypeError(
                f"'value' for {object_reference} must be True or False, is {type(value)}"
            )

        # Verify if value can be converted to float for input_registers and holding_registers:
        # This works for float, int, and string with valid number inside
        if object_reference in ("input_registers", "holding_registers"):

            # Verify encoding:
            if encoding not in ("h", "H", "e", "f"):
                raise ValueError(
                    f'encoding must be "h" (short), "H" (unsigned short), "e" (float16), or "f" (float32) not {encoding}'
                )

            if encoding in ("f"):
                value_bytes12 = value
                self.datastore.write(object_reference, address, value, encoding)
                self.datastore.write(object_reference, address + 1, value, encoding)

        self.datastore.write(object_reference, address, value, encoding)
