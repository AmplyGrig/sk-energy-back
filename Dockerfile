FROM python:3.6

RUN apt-get update \
  && apt-get -y install gcc

COPY ./ /opt/app

RUN pip install -r /opt/app/requirements.txt

WORKDIR /opt/app

CMD ["python3", "run.py"]

