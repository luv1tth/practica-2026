# Заметки — настольная программа и REST API

Учебный проект (учебная практика, тема «Основы веба и API»).
Проект состоит из двух частей:
- **настольная программа «Заметки»** (Python, Tkinter) с окном для создания, поиска, редактирования и удаления заметок;
- **сервер** — REST API на **Flask + SQLite**, к которому подключается программа: CRUD, поиск и пагинация. Сервер покрыт тестами (pytest), упакован в Docker и развёрнут на Render.

Программа хранит заметки на сервере, поэтому они доступны с любого компьютера.

**Демо:** https://ВАШ-СЕРВИС.onrender.com  ← заменить на свою ссылку после деплоя

Автор: Габышев Давид Юрьевич, группа Б-ИИПМИ-23, ИМИ СВФУ им. М.К. Аммосова.
Учебная практика, 22.06.2026 – 04.07.2026. Руководитель: Акимов Мир Петрович.

## Настольная программа

```bash
python desktop/notes_app.py   # для локальной работы сначала запустите сервер: python wsgi.py
```
В поле **Сервер** укажите адрес API (локально `http://127.0.0.1:5000` или ссылку на Render) и нажмите **Подключиться**. Горячие клавиши: `Ctrl+N` — новая заметка, `Ctrl+S` — сохранить.

Готовый **NotesApp.exe** для Windows собирается автоматически: вкладка **Actions → build-exe → последний запуск → Artifacts → NotesApp-windows**.
Чтобы программа сразу подключалась к вашему серверу, впишите его адрес в `DEFAULT_URL` в файле `desktop/notes_app.py`.

Собрать .exe вручную:
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name NotesApp desktop/notes_app.py
```
Файл появится в папке `dist/`.

## Стек
- Python 3.12, Tkinter — настольная программа
- Flask 3
- SQLite (модуль `sqlite3`)
- pytest — тесты
- gunicorn — WSGI-сервер для продакшена
- Docker — контейнеризация
- Render — хостинг

## Структура проекта
```
notes-api/
├── .github/workflows/
│   ├── tests.yml     # автозапуск тестов
│   └── build-exe.yml # сборка NotesApp.exe для Windows
├── desktop/
│   ├── notes_app.py  # настольная программа (Tkinter)
│   └── api_client.py # клиент REST API
├── app/
│   ├── __init__.py   # фабрика приложения, обработчики ошибок, CORS
│   ├── db.py         # подключение к SQLite и схема таблицы
│   ├── routes.py     # эндпоинты /api/notes
│   └── static/index.html  # демо-страница для работы с API из браузера
├── tests/
│   ├── conftest.py   # фикстура тестового клиента с временной БД
│   ├── test_notes.py # тесты API
│   └── test_client.py # тесты клиента программы на живом сервере
├── postman_collection.json
├── wsgi.py           # точка входа
├── requirements.txt
├── Dockerfile
├── render.yaml       # настройки деплоя на Render
└── pytest.ini
```

## Эндпоинты

| Метод  | URL                   | Описание                         | Ответ |
|--------|-----------------------|----------------------------------|-------|
| GET    | `/`                   | Демо-страница (HTML)             | 200 |
| GET    | `/health`             | Проверка работы сервиса          | 200 |
| GET    | `/api/notes`          | Список заметок (`q`, `page`, `per_page`) | 200 |
| GET    | `/api/notes/<id>`     | Одна заметка                     | 200 / 404 |
| POST   | `/api/notes`          | Создать заметку                  | 201 / 400 |
| PUT    | `/api/notes/<id>`     | Полностью заменить заметку       | 200 / 400 / 404 |
| PATCH  | `/api/notes/<id>`     | Частично обновить заметку        | 200 / 400 / 404 |
| DELETE | `/api/notes/<id>`     | Удалить заметку                  | 204 / 404 |

Формат заметки:
```json
{
  "id": 1,
  "title": "Купить молоко",
  "content": "2 литра",
  "created_at": "2026-10-19 10:00:00",
  "updated_at": "2026-10-19 10:00:00"
}
```

## Примеры запросов (curl)

```bash
# создать
curl -X POST http://localhost:5000/api/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "Купить молоко", "content": "2 литра"}'

# список (2-я страница по 5 штук)
curl "http://localhost:5000/api/notes?page=2&per_page=5"

# поиск
curl "http://localhost:5000/api/notes?q=молоко"

# получить одну
curl http://localhost:5000/api/notes/1

# частично обновить
curl -X PATCH http://localhost:5000/api/notes/1 \
  -H "Content-Type: application/json" \
  -d '{"content": "3 литра"}'

# удалить
curl -X DELETE http://localhost:5000/api/notes/1
```

Те же запросы есть в `postman_collection.json` — импортируйте в Postman (File → Import), переменная `base_url` задаёт адрес сервера.

## Локальный запуск

```bash
git clone https://github.com/ВАШ-ЛОГИН/notes-api.git
cd notes-api
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python wsgi.py
```
Сервис будет доступен на http://localhost:5000 (демо-страница там же).

## Тесты

```bash
pytest -v
```
Тесты также запускаются автоматически на GitHub при каждом push (вкладка **Actions**).

## Запуск в Docker

```bash
docker build -t notes-api .
docker run -p 8000:8000 notes-api
```
Сервис будет доступен на http://localhost:8000.

## Деплой на Render

В репозитории есть `render.yaml`, поэтому деплой делается в несколько кликов:

1. Зарегистрироваться на https://render.com через аккаунт GitHub.
2. **New → Blueprint** → выбрать этот репозиторий → **Apply**.
3. Подождать сборку (3–5 минут). Сервис получит адрес вида `https://notes-api-xxxx.onrender.com`.
4. Проверить: открыть адрес в браузере или `curl https://notes-api-xxxx.onrender.com/health`.

После каждого `git push` в ветку `main` Render пересобирает сервис автоматически.

> На бесплатном тарифе Render диск временный: при перезапуске SQLite-база очищается, а после 15 минут простоя сервис «засыпает» (первый запрос идёт ~30–50 сек). Для учебного демо это нормально; для постоянного хранения можно подключить PostgreSQL.

### Деплой на VPS (gunicorn + nginx)
```bash
pip install -r requirements.txt
screen -S notes
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
# Ctrl+A, D — отсоединиться от screen
```
Фрагмент конфига nginx:
```nginx
server {
    listen 80;
    server_name example.com;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```
