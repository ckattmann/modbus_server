import time
import socketserver
import struct
import threading

import stackprinter
from icecream import ic

datastore = {
    "coils": {},
    "discrete_inputs": {},
    "input_registers": {},
    "holding_registers": {},
}


def pack_bools_to_bits(bool_list):
    chars = []
    ic(bool_list)
    for j in range(0, len(bool_list), 8):
        bool_chunk = bool_list[j : j + 8]
        ic(j)
        ic(bool_chunk)
        equivalent_char = 0
        for i, b in enumerate(bool_chunk):
            if b:
                equivalent_char += 2 ** i
        chars.append(equivalent_char)

    ic(chars)
    return struct.pack(f"!{len(chars)}B", *chars)


class TCPHandler(socketserver.BaseRequestHandler):
    def handle(self):
        """Callback Function for requests to the TCP Server:"""

        print(
            f"Handling request from {self.client_address[0]},{self.client_address[1]}"
        )

        # Recv max 255 bytes, the maximal length for a Modbus frame:
        self.data = self.request.recv(255).strip()

        ## Extract Header + Function Code:
        # Transaction ID:   (2 Bytes)   Identifies the request-response-pair, is echoed in the response
        # Protocol:         (2 Bytes)   Always 0 (reserved for future use, lol)
        # Length:           (2 Bytes)   Length of the remaining frame in bytes (Total Length - 6)
        # Unit ID:          (1 Byte)    "Slave ID", inner identifier to route to different units (typically 0)
        # Function Code:    (1 Byte)    1,2,3,4,5,6,15,16,43: Read/Write input/register etc.
        transaction_id, protocol, length, unit_id, function_code = struct.unpack(
            "!HHHBB", self.data[:8]
        )
        ic(transaction_id)
        ic(protocol)
        ic(length)
        ic(unit_id)
        ic(function_code)

        ## Parse Function Code:
        if function_code in (1, 2, 3, 4):  # 'Read' Function Codes
            first_address = struct.unpack("!H", self.data[8:10])[0]
            number_of_registers = struct.unpack("!H", self.data[10:12])[0]
            ic(first_address)
            ic(number_of_registers)

        function_code_map = {
            1: "coils",
            2: "discrete_inputs",
            4: "input_registers",
            3: "holding_registers",
        }

        object_type = function_code_map[function_code]

        ## Walk through addresses and append to output array 'data':
        data = []
        for address in range(first_address, first_address + number_of_registers):
            try:
                ic(address)
                data.append(datastore[object_type][address])
                # TODO: Access redis instead of dict
            except KeyError:
                # TODO: Return error code
                pass

        ic(data)

        if object_type in ("input_registers", "holding_registers"):
            number_of_data_bytes = 2 * number_of_registers
            response_message_length = 3 + number_of_data_bytes
            data_bytes = struct.pack(f'{!{len(data)H}}', *data)

        if object_type in ("coils", "discrete_inputs"):
            data_bytes = pack_bools_to_bits(bool_list)

        # Response length is 3 fixed bytes (unit_id, function_code, number_of_data_bytes) plus the data bytes:
        response_message_length = 3 + len(data_bytes)

        ## Compose Response:
        response_items = [
            transaction_id,
            protocol,
            response_message_length,
            unit_id,
            function_code,
            number_of_data_bytes
        ]

        ## Pack response items into binary format, incl. the data items:
        response = struct.pack(f"!HHHBBB{len(data)}H", *response_items) + data_bytes

        self.request.sendall(response)


class Server:
    def __init__(self, host="localhost", port=502):
        self.host = host
        self.port = port

    def start_server_thread(self):
        while True:
            try:
                with socketserver.ThreadingTCPServer(
                    (self.host, self.port), TCPHandler
                ) as server:
                    server.serve_forever()
            except OSError:
                time.sleep(1)
                print(".", end="", flush=True)

    def start(self):
        server_thread = threading.Thread(target=self.start_server_thread).start()

    # TODO: Shortcut funcs for read_coil, read_input_register etc
    def set_coil(self, address, value):
        self.set_value(0, address, value)

    def set_value(self, object_reference, address, value):

        if type(object_reference) == str:
            object_reference = object_reference.lower()

        object_reference_map = {
            0: "coils",
            "coil": "coils",
            "do": "coils",
            1: "discrete_inputs",
            "discrete_input": "discrete_inputs",
            "di": "discrete_inputs",
            3: "input_registers",
            "input_register": "input_registers",
            "ai": "input_registers",
            4: "holding_registers",
            "holding_register": "holding_registers",
            "ao": "holding_registers",
        }
        try:
            object_type = object_reference_map[object_reference]
        except:
            pass
            # TODO: invalid object_reference:

        # TODO: Verify Address
        # TODO: Verify Value

        datastore[object_type][address] = value


if __name__ == "__main__":
    host = "localhost"
    port = 5020
    while True:
        try:
            with socketserver.TCPServer((host, port), TCPHandler) as server:
                server.serve_forever()
        except OSError:
            time.sleep(1)
            print(".", end="", flush=True)
