FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /usr/src/app
COPY requirements.txt ./
COPY . .
RUN pip install -r requirements.txt
RUN pip install confluent-kafka