![example workflow](https://github.com/oleffr/foodgram-project-react/actions/workflows/main.yml/badge.svg)

# _Foodgram_
## О проекте
>Foodgram - это социальная сеть для выставления своих рецептов (Ссылка на развернутый проект - https://foodgram-oleffr.hopto.org/signin)

## Запуск проекта
- Склонируйте репозиторий проекта (https://github.com/oleffr/foodgram-project-react):
```
 git clone git@github.com:oleffr/foodgram-project-react.git
```
- Запустите Docker Compose
```
docker compose -f docker-compose.yml up
```
- Cоберите статику
```
docker compose -f docker-compose.yml exec backend python manage.py collectstatic
docker compose -f docker-compose.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
- Примените миграции
```
docker compose -f docker-compose.yml exec backend python manage.py migrate
```

## Использованные пакеты приложений

>Django                       4.2.6
djangorestframework           3.14.0
postgres                      13.10
django-colorfield             0.10.1
djoser                        2.2.0
gunicorn                      20.1.0

## Об Авторе
Автор: Ольга Ефремова (github.com/oleffr)
