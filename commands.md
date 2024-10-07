
# After all configs run to build and start containers
docker-compose up -d --build
docker-compose build django

docker-compose up -d django
docker-compose stop django

# To get into container shell
docker exec -it django sh

# To run python manage.py django compands
python manage.py shell

python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Resources
https://medium.com/@runitranjankumar/django-docker-compose-celery-redis-postgresql-4c6a41e72973