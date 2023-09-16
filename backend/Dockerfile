FROM python:3.11-slim

RUN apt-get update && \
        apt-get upgrade -y && \
        apt-get install -y libpq-dev gcc

WORKDIR /app
COPY requirements.txt ./
RUN pip install -U pip && \
        pip install -r requirements.txt --no-cache-dir
COPY . .

CMD python manage.py migrate; \
    python manage.py collectstatic --noinput; \
    gunicorn -w 2 -b 0:8000 foodgram.wsgi;