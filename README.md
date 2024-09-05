# TP0: Docker + Comunicaciones + Concurrencia

Mariana Galdo Martinez

## Parte 1: Introducción a Docker

### Ejercicio N°1:

Para crear una definición de DockerCompose con una cantidad configurable de clientes, se definió un script de bash `generar-compose.sh`, ubicado en la raíz del proyecto. 

Para ejecutar el script, es necesario incluir por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

```bash
./generar-compose.sh docker-compose-dev.yaml 5
```

### Ejercicio N°2:
Para este ejercicio, se modificó el script `generar-compose.sh` para que cada archivo de configuración se persista en un volumen de Docker. 


### Ejercicio N°3:

Se definió un script de bash `validar-echo-server.sh` para verificar el correcto funcionamiento del servidor. Para usar el script, se necesita primero arrancar el container del servidor. 

```bash
$ make docker-compose-up
$ ./validar-echo-server.sh
```

### Ejercicio N°4:
Se modificaron tanto el servidor como el cliente para que terminen de forma _graceful_ al recibir la signal SIGTERM. 

## Parte 2: Repaso de Comunicaciones

### Ejercicio N°5:
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


### Ejercicio N°6:
#### Protocolo

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


### Ejercicio N°7:

#### Protocolo
Se mantiene el mismo protocolo que en el ejercicio 6, pero se agregan dos tipos de mensajes más para consultar el sorteo y recibir el resultado del sorteo. 

El cliente envía un mensaje `FinishedNotification` que consiste en solo un 1 byte que representa el ID de la agencia. 
El servidor responde a este mensaje con un mensaje de 4 bytes que representa la cantidad de ganadores de la agencia. 

#### Implementación

##### Flujo de Trabajo del Servidor

1. **Aceptar y almacenar conexiones:**
   - El servidor entra en un bucle donde acepta conexiones entrantes.
   - Cada vez que acepta una conexión, la guarda en una lista de sockets (`self.client_sockets`).
   - En este punto, no se procesan los mensajes; simplemente se mantiene la conexión abierta.

2. **Procesar mensajes de las conexiones abiertas:**
   - Después de haber aceptado todas las conexiones, el servidor comienza a iterar sobre la lista de conexiones abiertas.
   - Lee los mensajes de cada conexión. Esto se hace en un bucle donde se verifica cada socket para ver si ha enviado un mensaje.
   - Si un mensaje recibido es un `FinishedNotification`, el servidor registra esta notificación y realiza el procesamiento correspondiente.
   - Si el mensaje es otro tipo de mensaje (como una apuesta), el servidor lo procesa y almacena la información.

3. **Repetir la verificación hasta que se reciban todas las notificaciones:**
     - El servidor sigue iterando y procesando mensajes hasta que haya recibido todas las notificaciones esperadas o hasta que ocurra un timeout.
     - Se mantiene un registro de las notificaciones recibidas y se compara con el número esperado de agencias.
     - Una vez que todas las notificaciones han sido recibidas, el servidor procede a enviar los resultados del sorteo a cada cliente y se desconecta. 


## Parte 3: Repaso de Concurrencia

### Ejercicio N°8:

#### Flujo de Trabajo del Servidor
##### Proceso Principal (Main Process)

- El proceso principal es responsable de inicializar el servidor, aceptar conexiones entrantes de los clientes y crear procesos hijos para manejar cada conexión de cliente.

##### Procesos Hijos (Child Processes)

- Cada proceso hijo maneja una conexión con un cliente.
- El cliente envía varias apuestas en batches (lotes), y el proceso hijo recibe y envía estas apuestas al servidor para su procesamiento. Una vez que el cliente termina de enviar sus apuestas, envía un mensaje de "notificación de finalización" (FinishedNotification). Después de esto, el proceso hijo espera en la barrera.

##### Barrera

La barrera se utiliza para sincronizar la finalización de todos los clientes. En este caso, la barrera asegura que todos los clientes hayan enviado su `FinishedNotification` antes de proceder con el sorteo y el cálculo de los ganadores. Solo cuando todos los procesos hijos han alcanzado la barrera (es decir, todos los clientes han terminado de enviar sus apuestas), el servidor procede a realizar el sorteo.

###### Rol de la Barrera:
- Sincronización Final: La barrera asegura que todos los procesos hijos hayan completado la recepción de apuestas y enviado su FinishedNotification.
- Cálculo de Ganadores: Una vez que la barrera se libera, el proceso principal sabe que todas las apuestas han sido enviadas, y puede proceder con el cálculo de ganadores.

##### Proceso Trabajador:
- Procesa el flujo de apuestas de manera asíncrona y continua.
- Este proceso está diseñado para manejar las apuestas conforme son recibidas, almacenarlas y procesarlas sin bloquear la ejecución de otros procesos.
- El proceso de trabajador opera de forma independiente de los procesos hijos. Esto significa que las apuestas pueden procesarse mientras los clientes aún están enviando más datos, mejorando la eficiencia.

##### Sorteo (Winner Calculation):

Una vez que todos los procesos hijos han finalizado (confirmado por la barrera), el proceso principal realiza el cálculo del sorteo y determina los ganadores.
El servidor puede enviar los resultados a cada cliente individualmente después de que el sorteo haya concluido. Cuando se concluye el sorteo, se cierran los clientes y el servidor. 
