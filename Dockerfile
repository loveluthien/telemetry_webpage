FROM python:3.13-slim
COPY . ./
RUN pip install -r requirements.txt
# CMD gunicorn -c gunicorn.config.py main:server
