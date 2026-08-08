# ASET Worker Extension

Это semantic bootstrap границы продуктивной работы ASET.

Минимальная машина работы:

```text
UNREGISTERED -> ACCEPTED -> RUNNING -> (RESULT XOR NO_RESULT)
```

`NO_RESULT` — положительно зафиксированный терминальный исход, а не отсутствие записи. Пока работа находится в `RUNNING`, отсутствие результата означает только то, что терминальный исход ещё не зарегистрирован.

`RESULT` не означает «успех», а `NO_RESULT` не означает «провал». Семантика Worker отвечает только на вопрос, был ли произведён exact result material для exact work invocation.

Worker, его вычислительная/когнитивная/материальная способность, результат и evidence сами по себе не создают Authority, Seed Resolution, признанное изменение Context или разрешение на внешний эффект.

Локальная bootstrap-проверка:

```bash
python tools/run_local_gate.py
```

Canon-to-TLA equivalence и механически доказанное Seed refinement пока намеренно остаются открытыми release gates.
