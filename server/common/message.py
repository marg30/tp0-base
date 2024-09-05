class Message:
    def __init__(self, name, last_name, id_document, birth_date, number):
        self.name = name
        self.last_name = last_name
        self.id_document = id_document
        self.birth_date = birth_date
        self.number = number

    @classmethod
    def decode(cls, bytes_arr):
        offset = 0
        name, offset = cls._decode_string(bytes_arr, offset)
        last_name, offset = cls._decode_string(bytes_arr, offset)
        id_document, offset = cls._decode_id_document(bytes_arr, offset)
        birth_date, offset = cls._decode_birth_date(bytes_arr, offset)
        number, offset = cls._decode_number(bytes_arr, offset)

        return cls(name, last_name, id_document, birth_date, number), offset

    def __str__(self):
        return (
            f"\n--------------------------"
            f"\nName = {self.name}"
            f"\nLast Name = {self.last_name}"
            f"\nDocument ID = {self.id_document}"
            f"\nBirth Date = {self.birth_date}"
            f"\nNumber = {self.number}"
            f"\n--------------------------"
        )

    @classmethod
    def _decode_string(cls, bytes_arr, offset):
        length = int.from_bytes(bytes_arr[offset:offset + 1], byteorder='big')
        value = bytes_arr[offset + 1:offset + 1 + length].decode()
        return value, offset + 1 + length

    @classmethod
    def _decode_id_document(cls, bytes_arr, offset):
        id_document = int.from_bytes(bytes_arr[offset:offset + 8], byteorder='big')
        return id_document, offset + 8

    @classmethod
    def _decode_birth_date(cls, bytes_arr, offset):
        return bytes_arr[offset:offset + 10].decode(), offset + 10

    @classmethod
    def _decode_number(cls, bytes_arr, offset):
        number = int.from_bytes(bytes_arr[offset:offset + 4], byteorder='big')
        return number, offset + 4


class ACKMessage:
    def __init__(self, batch_id, number):
        self.batch_id = batch_id
        self.number = number

    def encode(self):
        return (
                self.batch_id.to_bytes(4, byteorder='big') +
                self.number.to_bytes(4, byteorder='big')
        )


class WinnerMessage:
    def __init__(self, amount):
        self.amount = amount

    def encode(self):
        return self.amount.to_bytes(4, byteorder='big')


class BatchMessage:
    def __init__(self, client_id, batch_id, messages):
        self.client_id = client_id
        self.batch_id = batch_id
        self.messages = messages

    @classmethod
    def decode(cls, bytes_arr):
        offset = 0
        client_id = int.from_bytes(bytes_arr[offset:offset + 1], byteorder='big')
        offset += 1
        batch_id = int.from_bytes(bytes_arr[offset:offset + 4], byteorder='big')
        offset += 4
        num_messages = int.from_bytes(bytes_arr[offset:offset + 4], byteorder='big')
        offset += 4

        messages = []
        for _ in range(num_messages):
            message, next_offset = Message.decode(bytes_arr[offset:])
            offset += next_offset
            messages.append(message)

        return cls(client_id, batch_id, messages)


class FinishedNotification:
    def __init__(self, client_id):
        self.client_id = client_id

    @classmethod
    def decode(cls, bytes_arr):
        client_id = int.from_bytes(bytes_arr[0:1], byteorder='big')
        return cls(client_id)