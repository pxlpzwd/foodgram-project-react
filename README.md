## Проект Foodgram https://foodgrams.didns.ru/

### пароль и логин от админки

- login: root
- pswd: Metalik86

### Для локально развёртывание проекта нужно:

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

- Пересобрать образ:

```text
Запустить из католога infra файл
docker-compose up --build
```

- Сделать миграции:

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
### Для  развёртывания на сервере:
- Нужно сделать 
```text
1. Настроить nginx на локально и на серврее
2. Добавить Secrets* на https://github.com/ в репазитории проекта
2. Раскоментировать файл #main.yml 
3. выполнить команду git add .
4. git commit -a -m 'коментарий'
5. git push 
```
```text
Скрипт main.yml развернёт автоматом проект на сервере
```