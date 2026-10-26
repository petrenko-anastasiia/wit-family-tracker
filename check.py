"""Одна команда перевірки: bean-check + контрольні цифри Олі й Марка.
Запуск: uv run python check.py"""
import subprocess, sys
from decimal import Decimal
from budget import LEDGER, load, summary

CONTROL = {("Оля", 8): Decimal("2195.21"), ("Оля", 9): Decimal("2582.42"),
           ("Марко", 8): Decimal("1855.57"), ("Марко", 9): Decimal("2432.83")}

r = subprocess.run(["bean-check", str(LEDGER)], capture_output=True, text=True)
print("bean-check:", "OK (без повідомлень)" if r.returncode == 0 and not (r.stdout + r.stderr).strip()
      else "ПОМИЛКИ\n" + r.stdout + r.stderr)
ok = r.returncode == 0
out, owed = summary(load()[0])
for (who, month), want in CONTROL.items():
    got = out[(2026, month)][who]["variable"]
    mark = "OK" if got == want else "НЕ ЗБІГАЄТЬСЯ"
    ok &= got == want
    print(f"{who:6} 2026-{month:02d} змінні: {got:>9.2f} зл (контроль {want}) {mark}")
for (y, m), v in sorted(owed.items()):
    txt = f"Марко винен Олі {v:.2f} зл" if v >= 0 else f"Оля винна Марку {-v:.2f} зл"
    print(f"Спільні {y}-{m:02d}: {txt}")
sys.exit(0 if ok else 1)
