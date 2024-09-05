# TP0: Docker + Comunicaciones + Concurrencia

Mariana Galdo Martinez (105658)

### Ejercicio N°1:

Para crear una definición de DockerCompose con una cantidad configurable de clientes, se definió un script de bash `generar-compose.sh`, ubicado en la raíz del proyecto. 

Para ejecutar el script, es necesario incluir por parámetro el nombre del archivo de salida y la cantidad de clientes esperados:

```bash
./generar-compose.sh docker-compose-dev.yaml 5
``
