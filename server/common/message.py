class Message:
    def __init__(self, client_id, name, last_name, id_document, birth_date, number):
        self.client_id = client_id
        self.name = name
        self.last_name = last_name
        self.id_document = id_document
        self.birth_date = birth_date
        self.number = number

    def encode(self):
        client_id_bytes = self.client_id.to_bytes(1, byteorder='big')
        name_bytes = self.name.encode()
        last_name_bytes = self.last_name.encode()
        id_document_bytes = self.id_document.to_bytes(8, byteorder='big')
        birth_date_bytes = self.birth_date.encode()
        number_bytes = self.number.to_bytes(4, byteorder='big')
        bytes_arr = (
            client_id_bytes + 
            len(name_bytes).to_bytes(1, byteorder='big') + name_bytes + 
            len(last_name_bytes).to_bytes(1, byteorder='big') + last_name_bytes +
            id_document_bytes + 
            birth_date_bytes + 
            len(number_bytes).to_bytes(1, byteorder='big') + number_bytes
        )

        return bytes_arr

    @classmethod
    def decode(cls, bytes_arr):
        client_id = int.from_bytes(bytes_arr[0:1], byteorder='big')
        name_length = int.from_bytes(bytes_arr[1:2], byteorder='big')
        name = bytes_arr[2:2 + name_length].decode()
        last_name_offset = 2 + name_length
        last_name_length = int.from_bytes(bytes_arr[last_name_offset:last_name_offset + 1], byteorder='big')
        last_name = bytes_arr[last_name_offset + 1:last_name_offset + 1 + last_name_length].decode()

        id_document_offset = last_name_offset + 1 + last_name_length
        id_document = int.from_bytes(bytes_arr[id_document_offset:id_document_offset + 8], byteorder='big')

        birth_date_offset = id_document_offset + 8
        birth_date = bytes_arr[birth_date_offset:birth_date_offset + 10].decode()

        number_offset = birth_date_offset + 10
        number = int.from_bytes(bytes_arr[number_offset:number_offset + 4], byteorder='big')

        return cls(client_id, name, last_name, id_document, birth_date, number)
    
    def __str__(self):
        return f"\n--------------------------\
                \nName = {self.name}\
                \nLast Name = {self.last_name}\
                \nDocument ID = {self.id_document}\
                \nBirth Date = {self.birth_date}\
                \nNumber = {self.number}\
                \n--------------------------"
    

class ACKMessage:
    def __init__(self, batch_id, number):
        self.batch_id = batch_id
        self.number = number

    def encode(self):
        batch_id_bytes = self.batch_id.to_bytes(4, byteorder='big')
        number_bytes = self.number.to_bytes(4, byteorder='big')
        bytes_arr = (
            batch_id_bytes + 
            number_bytes
        )
        return bytes_arr

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
        client_id = int.from_bytes(bytes_arr[0:1], byteorder='big')
        batch_id = int.from_bytes(bytes_arr[1:5], byteorder='big')
        number_messages = int.from_bytes(bytes_arr[5:9], byteorder='big')
        previous_message_offset = 9
        messages = []
        for i in range(number_messages):
            name_length = int.from_bytes(bytes_arr[previous_message_offset:previous_message_offset+1], byteorder='big')
            name_offset = previous_message_offset + 1
            name = bytes_arr[name_offset:name_offset + name_length].decode()
            last_name_offset = name_offset + name_length
            last_name_length = int.from_bytes(bytes_arr[last_name_offset:last_name_offset + 1], byteorder='big')
            last_name = bytes_arr[last_name_offset + 1:last_name_offset + 1 + last_name_length].decode()

            id_document_offset = last_name_offset + 1 + last_name_length
            id_document = int.from_bytes(bytes_arr[id_document_offset:id_document_offset + 8], byteorder='big')

            birth_date_offset = id_document_offset + 8
            birth_date = bytes_arr[birth_date_offset:birth_date_offset + 10].decode()

            number_offset = birth_date_offset + 10
            number = int.from_bytes(bytes_arr[number_offset:number_offset + 4], byteorder='big')

            previous_message_offset = number_offset + 4
            msg = Message(client_id, name, last_name, id_document, birth_date, number)
            messages.append(msg)

        return cls(client_id, batch_id, messages)
    

class FinishedNotification:
    def __init__(self, client_id):
        self.client_id = client_id

    @classmethod
    def decode(cls, bytes_arr):
        client_id = int.from_bytes(bytes_arr[0:1], byteorder='big')
        return cls(client_id)