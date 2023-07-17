FROM python:3.11
EXPOSE 5000
WORKDIR /rest_api_ex
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt && apt-get update && apt-get install -y iputils-ping
COPY . .
CMD ["/bin/sh", "docker-entrypoint.sh"]