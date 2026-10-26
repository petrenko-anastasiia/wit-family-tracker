"""Спільна логіка підсумків: змінні/фіксовані витрати по людях і хто кому винен."""
from collections import defaultdict
from decimal import Decimal
from pathlib import Path
from beancount import loader
from beancount.core import data

LEDGER = Path(__file__).parent / "main.beancount"
PEOPLE = ("Оля", "Марко")


def load():
    entries, errors, _ = loader.load_file(str(LEDGER))
    return entries, errors


def summary(entries):
    """{(рік, місяць): {особа: {fixed, variable, income, cats{}}}} + спільні борги."""
    out = defaultdict(lambda: {p: {"fixed": Decimal(0), "variable": Decimal(0), "income": Decimal(0),
                                   "cats": defaultdict(Decimal)} for p in PEOPLE})
    owed = defaultdict(Decimal)  # (рік, місяць) -> скільки Марко винен Олі (мінус = навпаки)
    for e in entries:
        if not isinstance(e, data.Transaction):
            continue
        key = (e.date.year, e.date.month)
        for p in e.postings:
            parts = p.account.split(":")
            if len(parts) < 3 or parts[1] not in PEOPLE:
                continue
            who, n = parts[1], p.units.number
            if parts[0] == "Expenses":
                out[key][who]["fixed" if "fixed" in e.tags else "variable"] += n
                out[key][who]["cats"][":".join(parts[2:])] += n
            elif parts[0] == "Income":
                out[key][who]["income"] -= n
        if "shared" in e.tags:
            share = Decimal(e.meta.get("other_share", "0.5"))
            paid = sum(p.units.number for p in e.postings if p.account.startswith("Expenses:"))
            payer = e.meta.get("payer")
            owed[key] += paid * share if payer == "Оля" else -paid * share
    return out, owed
