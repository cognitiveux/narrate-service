FROM python:3.10.8
RUN mkdir /code
WORKDIR /code
ADD . /code
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
