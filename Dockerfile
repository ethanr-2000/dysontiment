FROM python:3

WORKDIR /app

COPY /src /app/src

RUN pip install -r /app/requirements.txt

ENV AM_I_IN_A_DOCKER_CONTAINER Yes

CMD python3 /app/dysontiment.py
