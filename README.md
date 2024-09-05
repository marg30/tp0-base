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

El cliente envía un mensaje FinishedNotification que consiste en solo un 1 byte que representa el ID de la agencia. 
El servidor responde a este mensaje con un mensaje de 4 bytes que representa la cantidad de ganadores de la agencia. 

## Parte 3: Repaso de Concurrencia

### Ejercicio N°8:



## Consideraciones Generales
Se espera que los alumnos realicen un _fork_ del presente repositorio para el desarrollo de los ejercicios.El _fork_ deberá contar con una sección de README que indique como ejecutar cada ejercicio.

La Parte 2 requiere una sección donde se explique el protocolo de comunicación implementado.
La Parte 3 requiere una sección que expliquen los mecanismos de sincronización utilizados.

Cada ejercicio deberá resolverse en una rama independiente con nombres siguiendo el formato `ej${Nro de ejercicio}`. Se permite agregar commits en cualquier órden, así como crear una rama a partir de otra, pero al momento de la entrega deben existir 8 ramas llamadas: ej1, ej2, ..., ej7, ej8.

(hint: verificar listado de ramas y últimos commits con `git ls-remote`)

Puden obtener un listado del último commit de cada rama ejecutando `git ls-remote`.

Finalmente, se pide a los alumnos leer atentamente y **tener en cuenta** los criterios de corrección provistos [en el campus](https://campusgrado.fi.uba.ar/mod/page/view.php?id=73393).
