# name: CI for Foodgram

# on:
#   push:
#     branches: [ master ]

# jobs:
#   copy_files_to_server:
#     name: Copy infra and docs
#     runs-on: ubuntu-22.04
#     steps:
#     - uses: actions/checkout@v2

#     - name: Create projects directory
#       uses: appleboy/ssh-action@master
#       with:
#         host: ${{ secrets.HOST }}
#         username: ${{ secrets.USERNAME }}
#         key: ${{ secrets.PRIVATE_KEY }}
#         passphrase: ${{ secrets.SSH_PASSPHRASE }}
#         # script: cd projects && mkdir -p foodgram && mkdir -p foodgram/docs
#         #script: mkdir -p projects/foodgram/docs && cd projects && ls -la
#         script: sudo mkdir -p /${{ secrets.USERNAME }}/projects/foodgram/docs && cd /${{ secrets.USERNAME }}/projects && ls -la

#     - name: Copy infra files
#       uses: appleboy/scp-action@master
#       with:
#           source: infra/
#           target: /${{ secrets.USERNAME }}/projects/foodgram/
#           host: ${{ secrets.HOST }}
#           username: ${{ secrets.USERNAME }}
#           key: ${{ secrets.PRIVATE_KEY }}
#           passphrase: ${{ secrets.SSH_PASSPHRASE }}

#     - name: Copy docs
#       uses: appleboy/scp-action@master
#       with:
#           source: docs
#           target: /${{ secrets.USERNAME }}/projects/foodgram/docs/
#           host: ${{ secrets.HOST }}
#           username: ${{ secrets.USERNAME }}
#           key: ${{ secrets.PRIVATE_KEY }}
#           passphrase: ${{ secrets.SSH_PASSPHRASE }}

#   build_push_backend_to_DockerHub:
#     name: Building back image and pushing it to Docker Hub
#     runs-on: ubuntu-22.04
#     steps:
#     - uses: actions/checkout@v2

#     - name: Set up Docker Buildx
#       uses: docker/setup-buildx-action@v1

#     - name: Login to Docker
#       uses: docker/login-action@v1
#       with:
#         username: ${{ secrets.DOCKER_USER }}
#         password: ${{ secrets.DOCKER_PASS }}

#     - name: Push "foodgram/backend" to DockerHub
#       uses: docker/build-push-action@v2
#       with:
#         context: backend/
#         push: true
#         tags: ${{ secrets.DOCKER_USER }}/foodgram_back:latest

#   build_push_frontend_to_DockerHub:
#     name: Building front image and pushing it to Docker Hub
#     runs-on: ubuntu-22.04
#     steps:
#     - uses: actions/checkout@v2

#     - name: Set up Docker Buildx
#       uses: docker/setup-buildx-action@v1

#     - name: Login to Docker
#       uses: docker/login-action@v1
#       with:
#         username: ${{ secrets.DOCKER_USER }}
#         password: ${{ secrets.DOCKER_PASS }}

#     - name: Push "foodgram/frontend" to DockerHub
#       uses: docker/build-push-action@v2
#       with:
#         context: frontend/
#         push: true
#         tags: ${{ secrets.DOCKER_USER }}/foodgram_front:latest

#   deploy:
#     runs-on: ubuntu-22.04
#     needs:
#       - copy_files_to_server
#       - build_push_backend_to_DockerHub
#       - build_push_frontend_to_DockerHub
#     steps:
#     - name: remote ssh commands to deploy
#       uses: actions/checkout@v3
#        # Копируем docker-compose.production.yml на продакшен-сервер
#     - name: Copy docker-compose.yml via ssh
#       uses: appleboy/ssh-action@master
#       with:
#         host: ${{ secrets.HOST }}
#         username: ${{ secrets.USERNAME }}
#         key: ${{ secrets.PRIVATE_KEY }}
#         passphrase: ${{ secrets.SSH_PASSPHRASE }}
#         # passphrase: ${{ secrets.PRIVATE_KEY_PASSPHRASE }}
#         #passphrase: NRjeSf
#         script: |
#           cd projects/foodgram/
#           echo DEBUG=${{ secrets.DEBUG }} > .env
#           echo SECRET_KEY=${{ secrets.SECRET_KEY }} >> .env
#           echo ALLOWED_HOSTS=${{ secrets.ALLOWED_HOSTS }} >> .env
#           echo CSRF_TRUSTED_ORIGINS=${{ secrets.CSRF_TRUSTED_ORIGINS }} >> .env
#           echo DB_ENGINE=${{ secrets.DB_ENGINE }} >> .env
#           echo DB_NAME=${{ secrets.DB_NAME }} >> .env
#           echo POSTGRES_USER=${{ secrets.POSTGRES_USER }} >> .env
#           echo POSTGRES_PASSWORD=${{ secrets.POSTGRES_PASSWORD }} >> .env
#           echo DB_HOST=${{ secrets.DB_HOST }} >> .env
#           echo DB_PORT=${{ secrets.DB_PORT }} >> .env

#           sudo docker-compose stop
#           sudo docker ps -a | grep Exit | cut -d ' ' -f 1 | xargs sudo docker rm
#           sudo docker rmi ${{ secrets.DOCKER_USER }}/foodgram_front
#           sudo docker rmi ${{ secrets.DOCKER_USER }}/foodgram_back
#           sudo docker-compose up -d
#           sudo docker image prune -a
#           rm -f .env

#   send_message:
#     runs-on: ubuntu-latest
#     needs: deploy
#     steps:
#     - name: send message
#       uses: appleboy/telegram-action@master
#       with:
#         to: ${{ secrets.TELEGRAM_TO }}
#         token: ${{ secrets.TELEGRAM_TOKEN }}
#         message: Деплой успешно выполнен!
