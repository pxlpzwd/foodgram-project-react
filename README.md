# Это набросок после ревью переделаю
- Download project with SSH

```text
git clone git@github.com:pxlpzwd/foodgram-project-react.git
```

- Создать env-file:

```text
touch .env
```

```text
- Заполните env-файл следующим образом:
DEBUG=True
#SECRET_KEY=<Your_some_long_string>
#ALLOWED_HOSTS=<Your_host>
#CSRF_TRUSTED_ORIGINS=https://<Your_host>
DB_ENGINE=django.db.backends.postgresql
DB_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
#DB_HOST=foodgram-db
DB_HOST=db
DB_PORT=5432
```

- Пересобрать образ из котолога infra

```text
docker-compose up --build
```

- Сделать миграции

```text
1. docker-compose exec backend bash
2. python manage.py makemigrations users
3. python manage.py makemigrations api
4. python manage.py makemigrations recipes
5. python manage.py migrate
```

- Сделать миграции  статики
```text
docker exec -it foodgram_backend python manage.py loaddata data/dump.json
```

