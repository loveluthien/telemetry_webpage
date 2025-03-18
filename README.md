This is `plotly` `dash` server for visualizing CARTA telemetry data.

`dash` app is running in the docker container. To build the docker image, run `docker build -t carta_telemetry .` under the cloned folder. Run docker container `docker run -p 4511:8051 --name carta_telemetry_container carta_telemetry`.