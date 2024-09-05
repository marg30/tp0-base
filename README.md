# TP0: Docker + Comunicaciones + Concurrencia

Mariana Galdo Martinez

## Ejercicio N°6:
### Protocolo

Para enviar un lote de apuestas, se modificó el protocolo de la siguiente manera. 
Se definió un nuevo tipo de Mensaje BatchMessage para que se envían los siguientes valores: 

1. Longitud del Paquete: 4 bytes que indican la longitud total del paquete.
2. ID Cliente: 1 byte que identifica al cliente.
3. ID Lote: 4 bytes para identificar al lote. 
4. Número de Apuestas en el Lote: 1 byte que indica cuántas apuestas están en el lote.

Luego, se envían las apuestas, siguiendo el mismo protocolo que en el ejercicio anterior.

La respuesta del servidor en este caso tiene un formato distinto. Se envían los siguientes valores:

1. Longitud del mensaje: 4 bytes que indican la longitud total de la respuesta.
2. ID del Lote: 4 bytes que representan el ID único del lote.
3. Número de Apuestas Registradas: 4 bytes que indican cuántas apuestas del lote se registraron exitosamente.
