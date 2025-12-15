# TELEGRAM STORE

 Телеграм бот для продажи рыбы. Backend работает на strapi.

## Установка и запуск

### Скачать проект
```commandline
git clone https://github.com/Aleksashka301/telegram_store
```

### Перейти в проект
```commandline
cd telegram_store
```

### Установка виртуального окружения
Для работы проекта рекомендуется python версии 3.8, либо новее, но не новее 3.12.
```commandline
python -m venv myvenv
```

### Активация виртуального окружения
 windows
```commandline
myvenv\Scripts\activate
```

linux
```commandline
source myvenv/bin/activate
```

### Установка зависимостей
```commandline
pip install -r requirements.txt
```

### Переменные окружения
В корне проекта нужно создать файл `.env` и создать там переменную с токеном для телеграм.
- `TELEGRAM_TOKEN` телеграм токен, получить можно в телеграм у `@BotFather`

### BackEnd
Для работы strapi не обходим [node.js](https://nodejs.org/en/), проект тестировался на v16.16.0. Можно и другую версию,
но не ниже v10.0. Так же нужно установить npm, версия не имеет значения.

Установка yarn
```commandline
npm install --global yarn
```
Проверить установку yarn можно командой
```commandline
yarn --version
```

### Strapi
Нужно перейти в папку со strapi
```commandline
cd telegram_store
```
Запуск
```commandline
yarn develop
```
После запуска не закрывайте терминал. При первом запуске потребуется регистрация. Ознакомиться со strapi можно 
telegram_store -> README.md, [сайт](https://docs.strapi.io/), [GitHub](https://github.com/strapi/documentation)
Зайти в админ панель можно по адресу http://localhost:1337/admin

### Запуск
Запуск бота из корня проекта
```python
python main.py
```

