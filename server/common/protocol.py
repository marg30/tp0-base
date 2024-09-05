class Protocol:
    def __init__(self, client_sock):
        self.client_sock = client_sock
        self.client_sock.setblocking(0)
        self.client_sock.settimeout(2)

    def send_message(self, message: bytes):
        """
        Send a message with a header containing the length of the message.
        This method ensures that the message is sent completely, handling short writes.
        """
        message_length = len(message).to_bytes(4, byteorder='big')
        self._send_all(message_length)
        self._send_all(message)
    
    def receive_message(self) -> bytes:
        """
        Receive a message by first reading the length header, then the message itself.
        This method ensures that the message is received completely, handling short reads.
        """
        # Read the length header (4 bytes)
        length_data = self._recvall(4)
        if not length_data:
            raise ConnectionError("Failed to receive message length.")
        
        message_length = int.from_bytes(length_data, byteorder='big')
        try:
            message = self._recvall(message_length)
        except TimeoutError:
            message = ''
        return message

    def _send_all(self, data: bytes):
        """
        Ensures that all data is sent, handling short writes.
        """
        total_sent = 0
        while total_sent < len(data):
            sent = self.client_sock.send(data[total_sent:])
            if sent == 0:
                raise ConnectionError("Socket connection broken.")
            total_sent += sent

    def _recvall(self, size: int) -> bytes:
        """
        Ensures that all data is received, handling short reads.
        """
        data = b''
        while len(data) < size:
            part = self.client_sock.recv(size - len(data))
            if part == b'':
                raise ConnectionError("Socket connection broken.")
            data += part
        return data
