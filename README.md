# TP0: Docker + Comunicaciones + Concurrencia

Mariana Galdo Martinez

## Ejercicio N°8:

### Flujo de Trabajo del Servidor
#### Proceso Principal (Main Process)

- El proceso principal es responsable de inicializar el servidor, aceptar conexiones entrantes de los clientes y crear procesos hijos para manejar cada conexión de cliente.

#### Procesos Hijos (Child Processes)

- Cada proceso hijo maneja una conexión con un cliente.
- El cliente envía varias apuestas en batches (lotes), y el proceso hijo recibe y envía estas apuestas al servidor para su procesamiento. Una vez que el cliente termina de enviar sus apuestas, envía un mensaje de "notificación de finalización" (FinishedNotification). Después de esto, el proceso hijo espera en la barrera.

#### Barrera

La barrera se utiliza para sincronizar la finalización de todos los clientes. En este caso, la barrera asegura que todos los clientes hayan enviado su `FinishedNotification` antes de proceder con el sorteo y el cálculo de los ganadores. Solo cuando todos los procesos hijos han alcanzado la barrera (es decir, todos los clientes han terminado de enviar sus apuestas), el servidor procede a realizar el sorteo.

##### Rol de la Barrera
- Sincronización Final: La barrera asegura que todos los procesos hijos hayan completado la recepción de apuestas y enviado su FinishedNotification.
- Cálculo de Ganadores: Una vez que la barrera se libera, el proceso principal sabe que todas las apuestas han sido enviadas, y puede proceder con el cálculo de ganadores.

#### Proceso Trabajador
- Procesa el flujo de apuestas de manera asíncrona y continua.
- Este proceso está diseñado para manejar las apuestas conforme son recibidas, almacenarlas y procesarlas sin bloquear la ejecución de otros procesos.
- El proceso de trabajador opera de forma independiente de los procesos hijos. Esto significa que las apuestas pueden procesarse mientras los clientes aún están enviando más datos, mejorando la eficiencia.

#### Sorteo

Una vez que todos los procesos hijos han finalizado (confirmado por la barrera), el proceso principal realiza el cálculo del sorteo y determina los ganadores.
El servidor puede enviar los resultados a cada cliente individualmente después de que el sorteo haya concluido. Cuando se concluye el sorteo, se cierran los clientes y el servidor. 
