FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY . /usr/src/app/
WORKDIR /usr/src/app
COPY requirements.txt ./
RUN pip install -r requirements.txt
RUN pip install confluent-kafka
RUN pip install python-decouple
RUN pip install flower
ENV DJANGO_SETTINGS_MODULE=core.settings
COPY .env /usr/src/app/.env
# Run migrations
RUN python manage.py makemigrations