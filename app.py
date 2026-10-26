"""WSGI-застосунок: вхід за паролем -> Fava (/) + мобільний звіт (/report).

Логін і пароль беруться лише зі змінних середовища TRACKER_USER і TRACKER_PASSWORD
(на PythonAnywhere їх завантажує WSGI-файл з ~/.tracker.env поза репозиторієм).
Без правильного входу жоден запит не доходить до даних.
"""
import base64, hmac, html, os
from pathlib import Path
from fava.application import create_app
from budget import LEDGER, load, summary

USER = os.environ.get("TRACKER_USER")
PASSWORD = os.environ.get("TRACKER_PASSWORD")
if not USER or not PASSWORD:
    raise RuntimeError("Задайте TRACKER_USER і TRACKER_PASSWORD у змінних середовища")
REQUIRE_HTTPS = os.environ.get("TRACKER_REQUIRE_HTTPS", "1") == "1"
MONTHS = ["", "Січень", "Лютий", "Березень", "Квітень", "Травень", "Червень", "Липень",
          "Серпень", "Вересень", "Жовтень", "Листопад", "Грудень"]

fava_app = create_app([str(LEDGER)], read_only=False)


def zl(v):
    return f"{v:,.2f}".replace(",", " ").replace(".", ",") + " зл"


def report_page():
    out, owed = summary(load()[0])
    secs = []
    for key in sorted(out, reverse=True):
        y, m = key
        blocks = []
        for who, s in out[key].items():
            exp = s["fixed"] + s["variable"]
            rate = f"{100 * (s['income'] - exp) / s['income']:.1f}%" if s["income"] else "—"
            cats = "".join(f"<tr><td>{html.escape(c)}</td><td>{zl(v)}</td></tr>"
                           for c, v in sorted(s["cats"].items(), key=lambda x: -x[1]))
            blocks.append(f"<h3>{who}</h3><p>Дохід {zl(s['income'])} · Витрати {zl(exp)} · "
                          f"<b>Норма заощаджень {rate}</b></p><p>Фіксовані {zl(s['fixed'])} · "
                          f"<b>Змінні {zl(s['variable'])}</b></p><table>{cats}</table>")
        v = owed.get(key, 0)
        debt = f"Марко винен Олі {zl(v)}" if v >= 0 else f"Оля винна Марку {zl(-v)}"
        secs.append(f"<details{' open' if not secs else ''}><summary>{MONTHS[m]} {y}</summary>"
                    f"<p class=d>Спільні (оренда, Kaufland/Auchan, інтернет, світло навпіл): {debt}</p>"
                    + "".join(blocks) + "</details>")
    return f"""<!doctype html><html lang=uk><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>Звіт</title>
<style>body{{font:16px system-ui;margin:12px;max-width:640px}}summary{{font-size:1.3em;font-weight:600;padding:8px 0}}
table{{width:100%;border-collapse:collapse}}td{{padding:3px;border-bottom:1px solid #ddd}}td+td{{text-align:right}}
.d{{background:#fff3cd;padding:8px}}a.b{{display:inline-block;padding:10px 14px;background:#1d4ed8;color:#fff;border-radius:8px;text-decoration:none;margin:4px 4px 4px 0}}</style>
<h1>Бюджет Олі і Марка</h1><a class=b href="./">Fava: додати готівку (кнопка +)</a>
{''.join(secs)}</html>""".encode()


def app(environ, start_response):
    if REQUIRE_HTTPS and environ.get("HTTP_X_FORWARDED_PROTO", environ.get("wsgi.url_scheme")) != "https":
        start_response("403 Forbidden", [("Content-Type", "text/plain; charset=utf-8")])
        return ["Лише HTTPS".encode()]
    ok = False
    auth = environ.get("HTTP_AUTHORIZATION", "")
    if auth.startswith("Basic "):
        try:
            u, _, p = base64.b64decode(auth[6:]).decode().partition(":")
            ok = hmac.compare_digest(u, USER) & hmac.compare_digest(p, PASSWORD)
        except Exception:
            ok = False
    if not ok:
        start_response("401 Unauthorized", [("WWW-Authenticate", 'Basic realm="tracker", charset="UTF-8"'),
                                            ("Content-Type", "text/plain; charset=utf-8")])
        return ["Потрібен вхід".encode()]
    sec = [("Strict-Transport-Security", "max-age=31536000"), ("Cache-Control", "no-store")]
    if environ.get("PATH_INFO") in ("/report", "/report/"):
        start_response("200 OK", [("Content-Type", "text/html; charset=utf-8")] + sec)
        return [report_page()]
    return fava_app(environ, lambda s, h, e=None: start_response(s, h + sec, e) if e else start_response(s, h + sec))


application = app
