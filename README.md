This is `plotly` `dash` server for visualizing CARTA telemetry data.

`dash` app is running in the docker container. To build the docker image, run `docker build -t carta_telemetry .` under the cloned folder. Run docker container `docker run -d -t -p 4511:8051 --name carta_telemetry_container carta_telemetry`.

`docker exec -d carta_telemetry_container gunicorn -c gunicorn.config.py main:server`


If the linux needs `sudo`, see [Manage Docker as a non-root user](https://docs.docker.com/engine/install/linux-postinstall/).