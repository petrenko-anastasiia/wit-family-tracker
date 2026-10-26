"""Імпорт виписок Олі (CSV банку Олі) і Марка (CSV польського банку) у Beancount.

Перезаписує transactions.beancount. Ручні операції (готівка з телефона)
Fava дописує в manual.beancount, імпорт їх не чіпає.
Запуск: uv run python import.py
"""
import csv, datetime
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).parent
DATA = ROOT / "data"
OUT = ROOT / "transactions.beancount"
CUR = "PLN"


def load_rules():
    with open(ROOT / "rules.csv", encoding="utf-8-sig", newline="") as f:
        return [(r["шаблон"].strip().lower(), r["рахунок"].strip(), r["фіксована"].strip().lower() == "так")
                for r in csv.DictReader(f) if r["шаблон"].strip()]


def load_shared():
    with open(ROOT / "shared.csv", encoding="utf-8-sig", newline="") as f:
        return [(r["шаблон"].strip().lower(), Decimal(r["частка_іншого"])) for r in csv.DictReader(f)]


def categorize(desc, amount, rules, person):
    text = desc.lower()
    for pattern, account, fixed in rules:
        if pattern in text:
            if amount > 0 and account.startswith("Expenses:"):
                return f"Income:{person}:Інше", False
            return account.replace(":", f":{person}:", 1), fixed
    return (f"Income:{person}:Інше" if amount > 0 else f"Expenses:{person}:Без-Категорії"), False


def pl_amount(s):
    return Decimal(s.replace("\xa0", "").replace(" ", "").replace(",", "."))


def read_olya(path):
    """CSV банку Олі: Completed Date, Amount, Fee, Balance, State, Product, Currency."""
    rows, seen = [], set()
    with open(path, encoding="utf-8-sig", newline="") as f:
        for r in csv.DictReader(f):
            if r["State"] != "COMPLETED" or r["Product"] != "Current" or r["Currency"] != CUR:
                continue
            key = (r["Completed Date"], r["Description"], r["Amount"], r["Balance"])
            if key in seen:
                continue
            seen.add(key)
            rows.append((datetime.date.fromisoformat(r["Completed Date"][:10]), r["Description"],
                         Decimal(r["Amount"]), Decimal(r["Fee"]), Decimal(r["Balance"])))
    return rows


def read_marko(path):
    """CSV банку Марка: шапка, далі `Data operacji;...;Kwota;Saldo po operacji`, нові зверху, кома в сумах."""
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Data operacji;"))
    rows = []
    for r in csv.DictReader(lines[start:], delimiter=";"):
        if not r.get("Data operacji"):
            continue
        d = datetime.datetime.strptime(r["Data operacji"], "%d.%m.%Y").date()
        rows.append((d, r["Opis"].strip(), pl_amount(r["Kwota"]), Decimal(0), pl_amount(r["Saldo po operacji"])))
    rows.reverse()  # банк дає нові зверху, сальдо рахуємо від старих
    return rows


def q(t):
    return '"' + t.replace('"', "'") + '"'


def m(n):
    return f"{n:.2f} {CUR}"


def ledger(person, rows, rules, shared, lines):
    bank = f"Assets:{person}:Банк"
    first = rows[0]
    opening = first[4] - first[2] + first[3]
    lines += [f'{first[0] - datetime.timedelta(days=1)} * "Початковий залишок {person}"',
              f"  {bank}  {m(opening)}", "  Equity:Початковий-Залишок", ""]
    month_end, unc = {}, []
    for date, desc, amount, fee, bal in rows:
        acc, fixed = categorize(desc, amount, rules, person)
        if acc.endswith("Без-Категорії"):
            unc.append(desc)
        tags = " #fixed" if fixed else ""
        share = next((s for p, s in shared if p in desc.lower()), None)
        if share is not None and amount < 0:
            tags += " #shared"
        lines.append(f"{date} * {q(desc)}{tags}")
        lines.append(f"  payer: {q(person)}")
        if share is not None and amount < 0:
            lines.append(f'  other_share: "{share}"')
        lines += [f"  {bank}  {m(amount - fee)}", f"  {acc}  {m(-amount)}"]
        if fee:
            lines.append(f"  Expenses:{person}:Комісії-Банку  {m(fee)}")
        lines.append("")
        month_end[(date.year, date.month)] = (date, bal)
    months = sorted(month_end)
    for i, (y, mo) in enumerate(months):
        last, bal = month_end[(y, mo)]
        when = datetime.date(y + mo // 12, mo % 12 + 1, 1) if i < len(months) - 1 else last + datetime.timedelta(days=1)
        lines.append(f"{when} balance {bank}  {m(bal)}")
    lines.append("")
    print(f"{person}: імпортовано {len(rows)} операцій, звірок: {len(months)}"
          + (f"; без категорії: {sorted(set(unc))}" if unc else ""))


def main():
    rules, shared = load_rules(), load_shared()
    lines = ["; Згенеровано import.py з data/, rules.csv і shared.csv. Руками не редагувати.", ""]
    ledger("Оля", read_olya(DATA / "olya-statement.csv"), rules, shared, lines)
    ledger("Марко", read_marko(DATA / "marko-statement.csv"), rules, shared, lines)
    OUT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
