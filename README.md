This is `plotly`-`dash` server for visualizing CARTA telemetry data.

1. The `dash` app is running in the docker container. To build the docker image, run `docker build -t carta_telemetry .` under the cloned folder. 
2. Run docker container `docker run -d -t -p 45xx:80xx --name carta_telemetry_container carta_telemetry`.
3. Start the telemetry `dash` app using `docker exec -d carta_telemetry_container gunicorn -c gunicorn.config.py main:server`.

If the linux needs `sudo`, see [Manage Docker as a non-root user](https://docs.docker.com/engine/install/linux-postinstall/).
Adding `url_base_pathname="/app_position/"` in the `dash.Dash` if using `Nginx` and it's `proxy_pass`. For example `http:url/app_position`.