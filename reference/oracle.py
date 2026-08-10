from __future__ import annotations
from copy import deepcopy

BASE = {
    "recognized": False,
    "code": "UNSET",
    "state_changed": False,
    "work_state": "UNREGISTERED",
    "authority_created": False,
    "effect_permitted": False,
    "seed_resolution_created": False,
}


def _result(**changes):
    out = dict(BASE)
    out.update(changes)
    return out


def state_of(work_id, started, terminal):
    t = terminal.get(work_id)
    if t is not None:
        return t["terminal_kind"]
    if work_id in started:
        return "RUNNING"
    return "UNREGISTERED"


def run_case(case):
    started = {}
    terminal = {}
    last = None

    for step in case["steps"]:
        kind = step["kind"]
        p = step["payload"]
        wid = p.get("work_id", "")

        if kind == "START_WORK":
            required = [
                p.get("work_id"),
                p.get("work_binding_digest"),
                p.get("worker_binding"),
                p.get("work_descriptor_binding"),
            ]
            if not all(required):
                last = _result(code="WORK_BINDING_REQUIRED")
                continue
            previous = started.get(wid)
            if previous is None:
                started[wid] = deepcopy(p)
                last = _result(
                    recognized=True,
                    code="WORK_STARTED",
                    state_changed=True,
                    work_state="RUNNING",
                )
            elif previous == p:
                last = _result(
                    recognized=True,
                    code="IDEMPOTENT_REPLAY",
                    work_state=state_of(wid, started, terminal),
                )
            else:
                last = _result(
                    code="WORK_IDENTITY_CONFLICT",
                    work_state=state_of(wid, started, terminal),
                )

        elif kind == "END_WORK":
            work = started.get(wid)
            if work is None:
                last = _result(code="WORK_NOT_STARTED")
                continue
            if p.get("work_binding_digest") != work.get("work_binding_digest"):
                last = _result(code="WORK_BINDING_MISMATCH", work_state=state_of(wid, started, terminal))
                continue
            terminal_kind = p.get("terminal_kind")
            if terminal_kind not in {"RESULT", "NO_RESULT"}:
                last = _result(code="TERMINAL_KIND_REQUIRED", work_state="RUNNING")
                continue
            if not p.get("terminal_record_digest") or not p.get("terminal_binding"):
                last = _result(code="TERMINAL_BINDING_REQUIRED", work_state="RUNNING")
                continue
            previous = terminal.get(wid)
            if previous is not None:
                if previous == p:
                    last = _result(
                        recognized=True,
                        code="IDEMPOTENT_REPLAY",
                        work_state=previous["terminal_kind"],
                    )
                else:
                    last = _result(
                        code="TERMINAL_WORK_IMMUTABLE",
                        work_state=previous["terminal_kind"],
                    )
                continue
            terminal[wid] = deepcopy(p)
            code = (
                "WORK_ENDED_WITH_RESULT"
                if terminal_kind == "RESULT"
                else "WORK_ENDED_WITH_NO_RESULT"
            )
            last = _result(
                recognized=True,
                code=code,
                state_changed=True,
                work_state=terminal_kind,
            )

        elif kind == "ASSERT_WORKER_AUTHORITY":
            last = _result(
                code="WORKER_AUTHORITY_FORBIDDEN",
                work_state=state_of(wid, started, terminal),
            )
        else:
            last = _result(
                code="UNKNOWN_OPERATION",
                work_state=state_of(wid, started, terminal),
            )

    return deepcopy(last)
