# Скопіюйте вміст у /var/www/<імʼя>_pythonanywhere_com_wsgi.py на PythonAnywhere.
# Секрети лежать у ~/.tracker.env (поза репозиторієм), формат: TRACKER_USER=... / TRACKER_PASSWORD=...
import os, sys
from pathlib import Path

HOME = Path.home()
PROJECT = HOME / "tracker"
for line in (HOME / ".tracker.env").read_text().splitlines():
    if "=" in line and not line.startswith("#"):
        k, v = line.split("=", 1)
        os.environ[k.strip()] = v.strip()
sys.path.insert(0, str(PROJECT))
os.chdir(PROJECT)
from app import application  # noqa: E402
