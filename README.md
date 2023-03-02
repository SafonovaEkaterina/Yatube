# Социальная сеть Yatube

Проект представляет социальную сеть и позволяет:
- Писать посты и делать публикации в отдельных группах
- Оформлять подписки на посты и авторов 
- Добавлять и удалять записи и комментарии к ним.

## Как запустить проект: 
- Склонируйте репозиторий:
```
git clone https://github.com/SafonovaEkaterina/Yatube.git
```
- Установите и активируйте виртуальное окружение:
```
python -m venv venv
source venv/Scripts/activate
```
- Установите зависимости из файла requirements.txt:
```
pip install -r requirements.txt
```
- Примените миграции:
```
python manage.py migrate
```
- В папке с файлом manage.py выполните команду:
```
python manage.py runserver
```
