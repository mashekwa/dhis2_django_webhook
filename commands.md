
# After all configs run to build and start containers
docker-compose up -d --build
docker-compose build django

docker-compose up -d django
docker-compose stop django

docker-compose build --no-cache

docker-compose up --build --no-cache 
docker-compose up --build --no-cache --force-recreate
docker-compose up --build --no-cache --remove-orphans


# To get into container shell
docker exec -it django sh

# CLEAN UP DOCKER
docker system prune -a

# To run python manage.py django compands
python manage.py shell

python manage.py makemigrations
python manage.py migrate

python manage.py collectstatic

# Create superuser
python manage.py createsuperuser

# Resources
https://medium.com/@runitranjankumar/django-docker-compose-celery-redis-postgresql-4c6a41e72973


# TEST CONNECTION TO KAFKA
telnet 10.51.73.144 9092

# SERVER BOX WEBHOOK
http://10.51.75.85:8000/webhooks/receive/

# DOCKER LOGS
docker logs -f --tail 10 dhis2_django_webhook-celery-1

10.51.75.70