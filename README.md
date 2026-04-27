# EDU-Web

Сайт вопросов и ответов на Django.

## Запуск

### Локально

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Открыть http://127.0.0.1:8000

### Docker

```bash
docker compose up --build
```

Открыть http://localhost:8000

## Страницы

На главной, `/hot/` и `/tag/.../` справа (на ширине ≥992px) отображается сайдбар: популярные теги и лучшие участники; на узкой ширине блок уходит под список вопросов.

- `/` - новые вопросы
- `/hot/` - популярные вопросы  
- `/tag/python/` - вопросы по тегу
- `/question/1/` - страница вопроса
- `/login/` - вход
- `/signup/` - регистрация
- `/profile/` - профиль
- `/ask/` - задать вопрос