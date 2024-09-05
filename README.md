# TP0: Docker + Comunicaciones + Concurrencia

Mariana Galdo Martinez

## Ejercicio N°5:
Para que cada container de cliente reciba las variables de entorno, se crearon cinco archivos `.env` y se modificó el script `generar-compose.sh` para que cada container use un archivo determinado.  

#### Protocolo

Se definieron dos tipos de mensajes, el mensaje Packet que envía el cliente con los datos de la apuesta y el mensaje ACK que envía el servidor cuando recibe la apuesta. 
El mensaje Packet tiene los siguientes datos:

1. Longitud del Paquete: 4 bytes que indican la longitud total del paquete.
2. ID Cliente: 1 byte que identifica al cliente.
3. Tamaño Nombre: 1 byte que indica el tamaño (en bytes) del campo de Nombre.
4. Nombre: N bytes que representan el nombre del participante (el tamaño N lo indica el campo Tamaño Nombre).
5. Tamaño Apellido: 1 byte que indica el tamaño (en bytes) del campo de Apellido.
6. Apellido: N bytes que representan el apellido del participante (el tamaño N lo indica el campo Tamaño Apellido).
7. Documento del Participante: 8 bytes que representan el documento del participante.
8. Fecha de Nacimiento: 10 bytes que representan la fecha de nacimiento del participante. 
9. Número de Apuesta: 4 bytes que representan el número de la apuesta.

La respuesta del servidor tiene el siguiente formato: 

1. Longitud del mensaje: 4 bytes que indican la longitud total de la respuesta.
2. Documento del Participante: 8 bytes que representan el documento del participante.
3. Número de Apuesta: 4 bytes que representan el número de la apuesta recibida.

Se definieron estos valores analizando los datos dados en el dataset. 
