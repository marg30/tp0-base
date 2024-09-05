# TP0: Docker + Comunicaciones + Concurrencia

Mariana Galdo Martinez

## Ejercicio N°7:

### Protocolo
Se mantiene el mismo protocolo que en el ejercicio 6, pero se agregan dos tipos de mensajes más para consultar el sorteo y recibir el resultado del sorteo. 

El cliente envía un mensaje `FinishedNotification` que consiste en solo un 1 byte que representa el ID de la agencia. 
El servidor responde a este mensaje con un mensaje de 4 bytes que representa la cantidad de ganadores de la agencia. 

### Implementación

#### Flujo de Trabajo del Servidor

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
