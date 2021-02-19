# Imports from stdlib:
import time
import socketserver
import struct
import threading
import logging

# Internal imports:
from . import modbus_datastore

socketserver.TCPServer.allow_reuse_address = True

logger = logging.getLogger("modbus_server_logger")
formatter = logging.Formatter("%(levelname)s: %(message)s")
streamhandler = logging.StreamHandler()
streamhandler.setLevel(logging.DEBUG)
streamhandler.setFormatter(formatter)
logger.addHandler(streamhandler)


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

    response = struct.pack(f"!HHHBBB", *response_items)
    return response


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """Callback Function for requests to the TCP Server:"""

        # Recv max 255 bytes, the maximal length for a Modbus frame:
        self.data = self.request.recv(255).strip()

        ## Extract Header + Function Code:
        # Transaction ID:   (2 Bytes)   Identifies the request-response-pair, is echoed in the response
        # Protocol:         (2 Bytes)   Always 0 ("reserved for future use", lol)
        # Length:           (2 Bytes)   Length of the remaining frame in bytes (Total Length - 6)
        # Unit ID:          (1 Byte)    "Slave ID", inner identifier to route to different units (typically 0)
        # Function Code:    (1 Byte)    1,2,3,4,5,6,15,16,43: Read/Write input/register etc.
        try:
            transaction_id, protocol, length, unit_id, function_code = struct.unpack(
                "!HHHBB", self.data[:8]
            )
        except struct.error:
            logger.error(f"Received incompatible bytes {self.data}")
            return

        # Pack header items into a tuple which can more easily be passed around:
        header_items = (transaction_id, protocol, length, unit_id, function_code)

        # Check if Function Code is valid:
        if function_code not in (1, 2, 3, 4):
            # Respond with exception 01 - Illegal Function:
            response = build_error_response(header_items, exception_code=1)
            self.request.sendall(response)
            return None

        if function_code in (1, 2, 3, 4):  # -> The 4 'Read' Function Codes
            first_address = struct.unpack("!H", self.data[8:10])[0]
            number_of_registers = struct.unpack("!H", self.data[10:12])[0]

        function_code_map = {
            1: "coils",
            2: "discrete_inputs",
            4: "input_registers",
            3: "holding_registers",
        }
        object_reference = function_code_map[function_code]

        ## Validate number of objects requested and respond with exception 3 if invalid:
        ## =============================================================================

        if object_reference in ("coils", "discrete_inputs"):
            if number_of_registers < 1 or number_of_registers > 2000:
                response = build_error_response(header_items, exception_code=3)
                self.request.sendall(response)
                return None

        if object_reference in ("input_registers", "holding_registers"):
            if number_of_registers < 1 or number_of_registers > 125:
                response = build_error_response(header_items, exception_code=3)
                self.request.sendall(response)
                return None

        ## Read addresses from datastore
        ## =============================

        try:
            # self.server is a reference to the socketserver.ThreadingTCPServer instance defined below:
            data = self.server.datastore.read(
                object_reference, first_address, number_of_registers
            )
        except KeyError:
            # Address not in datastore -> Respond with exception 02 - Illegal Data Address:
            response = build_error_response(header_items, exception_code=2)
            logger.warning(
                f"Request from {self.client_address[0]} for {object_reference}:{first_address} -> Modbus Error 2"
            )
            self.request.sendall(response)
            return
        except:
            logger.error(
                f"Request from {self.client_address[0]} for {object_reference}:{first_address} -> Modbus Error 4"
            )
            raise
            # Other Error -> Respond with exception 04 - Slave Device Failure:
            response = build_error_response(header_items, exception_code=4)
            self.request.sendall(response)
            return

        ## Compose response
        ## ================

        if object_reference in ("coils", "discrete_inputs"):
            data_bytes = pack_bools_to_bytes(data)

        if object_reference in ("input_registers", "holding_registers"):
            data_bytes = b"".join(data)

        # Response length is 3 fixed bytes (unit_id, function_code, number_of_data_bytes) plus the data bytes:
        response_message_length = 3 + len(data_bytes)
        number_of_data_bytes = len(data_bytes)

        # Compose response header
        response_items = [
            transaction_id,
            protocol,
            response_message_length,
            unit_id,
            function_code,
            number_of_data_bytes,
        ]

        # Pack response items into binary format and append data_bytes:
        response = struct.pack(f"!HHHBBB", *response_items) + data_bytes

        logger.debug(
            f"Request from {self.client_address[0]} for {object_reference}:{first_address}+{number_of_registers} -> Response {data_bytes}"
        )

        self.request.sendall(response)


class Server:
    def __init__(
        self, host="localhost", port=502, daemon=False, datastore=None, loglevel='INFO', autostart=False
    ):
        self.host = host
        self.port = port
        if datastore is None:
            self.datastore = modbus_datastore.DictDatastore()
        else:
            self.datastore = datastore
        self.daemon = daemon
        self.tcp_server = None
        streamhandler.setLevel(loglevel)
        if autostart:
            self.start()

    def _server_thread(self):
        try:
            self.tcp_server = socketserver.TCPServer((self.host, self.port), TCPHandler)
        except OSError:
            raise OSError(f"Could not start TCP server on port {self.port}")
        self.tcp_server.allow_reuse_address = True
        self.tcp_server.datastore = self.datastore
        self.tcp_server.serve_forever()

    def start(self):
        self.server_thread = threading.Thread(target=self._server_thread)
        # daemon == True -> Shutdown the thread when the main program exits
        self.server_thread.daemon = self.daemon
        self.server_thread.start()
        logger.info("Modbus Server started")

    def stop(self):
        if self.tcp_server:
            self.tcp_server.shutdown()
            self.tcp_server.server_close()
            self.tcp_server = None
        logger.info("Modbus Server stopped")

    def dump_datastore(self):
        return self.datastore.dump()

    ## Convenience Functions for direct access to object reference (single + multiple):
    ## ================================================================================

    def set_coil(self, address, value):
        self._set_value("coils", address, value)

    def set_coils(self, address, values):
        for value in values:
            self._set_value("coils", address, value)
            address += 1

    def set_discrete_input(self, address, value):
        self._set_value("discrete_inputs", address, value)

    def set_discrete_inputs(self, address, values):
        for value in values:
            self._set_value("discrete_inputs", address, value)
            address += 1

    def set_input_register(self, address, value, encoding):
        self._set_value("input_registers", address, value, encoding)

    def set_input_registers(self, address, values, encoding):
        for value in values:
            self._set_value("input_registers", address, value, encoding)
            address += struct.calcsize(encoding) // 2

    def set_holding_register(self, address, value, encoding):
        self._set_value("holding_registers", address, value, encoding)

    def set_holding_registers(self, address, values, encoding):
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
            if encoding not in ("h", "H", "e"):
                raise ValueError(
                    f'encoding must be "h"(short), "H"(unsigned short), or "e"(float16), not {encoding}'
                )

        self.datastore.write(object_reference, address, value, encoding)
