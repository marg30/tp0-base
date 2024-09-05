class Message:
    def __init__(self, client_id, name, last_name, id_document, birth_date, number):
        self.client_id = client_id
        self.name = name
        self.last_name = last_name
        self.id_document = id_document
        self.birth_date = birth_date
        self.number = number

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
    def __init__(self, id_document, number):
        self.id_document = id_document
        self.number = number

    def encode(self):
        id_document_bytes = self.id_document.to_bytes(8, byteorder='big')
        number_bytes = self.number.to_bytes(4, byteorder='big')
        bytes_arr = (
            id_document_bytes + 
            len(number_bytes).to_bytes(1, byteorder='big') + number_bytes
        )
        return bytes_arr
    