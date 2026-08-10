# ASET Worker Extension

Это минимальная semantic boundary продуктивной попытки ASET.

Базовый Worker теперь знает только два перехода:

```text
UNREGISTERED --START_WORK--> RUNNING --END_WORK(RESULT|NO_RESULT)--> terminal
```

Каноническое состояние append-only: сначала появляется exact immutable started-work binding, затем при завершении — один exact immutable terminal record. `RUNNING`, `RESULT` и `NO_RESULT` являются проекциями этих фактов.

`NO_RESULT` — явно зафиксированный терминальный исход, а не отсутствие записи. `RESULT` не означает успех, а `NO_RESULT` не означает провал.

Assignment, acceptance, очередь, scheduling, retry provenance, внутреннее устройство work descriptor, verification policy и качество результата находятся вне Worker canon и могут определяться профилями.

Worker, его способность, исполнение, результат и evidence сами по себе не создают Authority, Seed Resolution, признанное изменение Context или разрешение на внешний эффект.

Текущая semantic revision: `0.1.0-alpha.1` / `ASET-WORKER-CANON-0.1-ALPHA2`. После минимизации предыдущие materialized proofs намеренно не переносятся: formal closure должен быть выполнен заново для новой модели.

Локальная bootstrap-проверка:

```bash
python tools/run_local_gate.py
```
