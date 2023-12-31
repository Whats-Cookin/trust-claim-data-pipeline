# Use an official Python runtime as a parent image
FROM python:3.9

# Install cron
RUN apt-get update && apt-get -y install cron

WORKDIR /data/trust-claim-data-pipeline

COPY . .
RUN pip install --no-cache-dir -r requirements.txt


# Set up Crontab
COPY crontab.dev /etc/cron.d/my-crontab
RUN chmod 0644 /etc/cron.d/my-crontab
RUN crontab /etc/cron.d/my-crontab
RUN cron

# for the microservice
EXPOSE 5000

# Env variables expected to come from docker-compose
# this will not work locally without them, it needs a postgres database
# the docker compose file is in https://github.com/Whats-Cookin/trust_claim_backend

# for now just keep running to run crontab
CMD while true; do sleep 1000; done
# TODO when we have microservice start it here like
# CMD python ./app.py

