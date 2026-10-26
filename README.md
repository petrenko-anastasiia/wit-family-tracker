# Бюджет Олі і Марка (Beancount + Fava, WIT 5.0 ДЗ №3, частина 2)

Усі дані в репозиторії штучні (з умови завдання).

## Перевірка однією командою
```
uv run python check.py
```
Запускає `bean-check main.beancount` (має бути «OK (без повідомлень)») і друкує змінні витрати Олі й Марка
за серпень/вересень 2026 разом із контрольними цифрами (2195.21 / 2582.42 і 1855.57 / 2432.83), плюс хто кому винен за спільні витрати.

## Структура
- `data/olya-statement.csv`, `data/marko-statement.csv` — виписки (два різні формати).
- `import.py` — імпорт обох виписок → `transactions.beancount` (`uv run python import.py`).
- `rules.csv` — категорії; `фіксована=так` → тег `#fixed`. У Марка фіксовані: Orange, PGE, Zdrofit, YouTube Premium.
- `shared.csv` — спільні витрати навпіл (оренда, Kaufland, Auchan, інтернет, світло) → тег `#shared`.
- `manual.beancount` — сюди Fava пише готівку, додану з телефона (кнопка «+»).
- `app.py` — WSGI: вхід за паролем (HTTP Basic) перед усім, лише HTTPS, Fava на `/`, мобільний звіт на `/report`.
- `pythonanywhere_wsgi.py` — WSGI-файл для PythonAnywhere.

## Деплой на PythonAnywhere (безкоштовний акаунт)
1. Bash-консоль: `git clone https://github.com/<you>/<repo>.git ~/tracker && cd ~/tracker && python3.12 -m venv ~/.venvs/tracker && ~/.venvs/tracker/bin/pip install beancount beanquery fava`
2. Секрети поза репозиторієм: `printf 'TRACKER_USER=...\nTRACKER_PASSWORD=...\n' > ~/.tracker.env && chmod 600 ~/.tracker.env`
3. Web → Add a new web app → Manual configuration → Python 3.12. Virtualenv: `~/.venvs/tracker`.
4. Вставити вміст `pythonanywhere_wsgi.py` у WSGI configuration file, Reload.
5. Web → Security → увімкнути **Force HTTPS**. (Застосунок і сам відхиляє не-HTTPS запити.)
6. Відкрити `https://<імʼя>.pythonanywhere.com/report` — браузер попросить логін і пароль.

Локально: `TRACKER_USER=u TRACKER_PASSWORD=p TRACKER_REQUIRE_HTTPS=0 uv run python -c "from wsgiref.simple_server import make_server; from app import application; make_server('',8000,application).serve_forever()"`
