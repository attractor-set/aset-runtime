from __future__ import annotations
from copy import deepcopy

BASE = {
    "accepted": False,
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


def state_of(work_id, accepted, started, terminal):
    if work_id not in accepted:
        return "UNREGISTERED"
    t = terminal.get(work_id)
    if t is not None:
        return t["kind"]
    if work_id in started:
        return "RUNNING"
    return "ACCEPTED"


def run_case(case):
    accepted = {}
    started = set()
    terminal = {}
    last = None

    for step in case["steps"]:
        kind = step["kind"]
        p = step["payload"]
        wid = p.get("work_id", "")

        if kind == "ACCEPT_WORK":
            required = [
                p.get("work_id"), p.get("accepted_work_digest"), p.get("worker_binding"),
                p.get("context_binding"), p.get("work_spec_binding"), p.get("execution_constraints_binding")
            ]
            if not all(required):
                last = _result(code="WORK_BINDING_REQUIRED")
                continue
            previous = accepted.get(wid)
            if previous is None:
                # retry linkage, when declared, must point to an existing terminal record
                pred = p.get("predecessor_terminal_binding")
                if pred is not None:
                    if not any(t["terminal_record_digest"] == pred for t in terminal.values()):
                        last = _result(code="PREDECESSOR_TERMINAL_NOT_FOUND")
                        continue
                accepted[wid] = deepcopy(p)
                last = _result(accepted=True, code="WORK_ACCEPTED", state_changed=True, work_state="ACCEPTED")
            elif previous == p:
                last = _result(accepted=True, code="IDEMPOTENT_REPLAY", work_state=state_of(wid, accepted, started, terminal))
            else:
                last = _result(code="WORK_IDENTITY_CONFLICT", work_state=state_of(wid, accepted, started, terminal))

        elif kind == "START_WORK":
            a = accepted.get(wid)
            if a is None:
                last = _result(code="WORK_NOT_ACCEPTED")
            elif p.get("accepted_work_digest") != a.get("accepted_work_digest"):
                last = _result(code="ACCEPTED_WORK_BINDING_MISMATCH", work_state=state_of(wid, accepted, started, terminal))
            elif wid in terminal:
                last = _result(code="TERMINAL_WORK_IMMUTABLE", work_state=state_of(wid, accepted, started, terminal))
            elif wid in started:
                last = _result(code="WORK_ALREADY_RUNNING", work_state="RUNNING")
            else:
                started.add(wid)
                last = _result(accepted=True, code="WORK_STARTED", state_changed=True, work_state="RUNNING")

        elif kind in {"COMPLETE_WITH_RESULT", "COMPLETE_WITH_NO_RESULT"}:
            a = accepted.get(wid)
            if a is None:
                last = _result(code="WORK_NOT_ACCEPTED")
                continue
            if p.get("accepted_work_digest") != a.get("accepted_work_digest"):
                last = _result(code="ACCEPTED_WORK_BINDING_MISMATCH", work_state=state_of(wid, accepted, started, terminal))
                continue
            if wid not in started:
                last = _result(code="WORK_NOT_RUNNING", work_state="ACCEPTED")
                continue
            if wid in terminal:
                last = _result(code="TERMINAL_WORK_IMMUTABLE", work_state=state_of(wid, accepted, started, terminal))
                continue
            td = p.get("terminal_record_digest")
            if not td:
                last = _result(code="TERMINAL_BINDING_REQUIRED", work_state="RUNNING")
                continue
            if kind == "COMPLETE_WITH_RESULT":
                if not p.get("result_binding"):
                    last = _result(code="RESULT_BINDING_REQUIRED", work_state="RUNNING")
                    continue
                terminal[wid] = {"kind":"RESULT", **deepcopy(p)}
                last = _result(accepted=True, code="WORK_COMPLETED_WITH_RESULT", state_changed=True, work_state="RESULT")
            else:
                if not p.get("no_result_binding"):
                    last = _result(code="NO_RESULT_BINDING_REQUIRED", work_state="RUNNING")
                    continue
                if p.get("result_binding") is not None:
                    last = _result(code="NO_RESULT_CANNOT_CARRY_RESULT", work_state="RUNNING")
                    continue
                terminal[wid] = {"kind":"NO_RESULT", **deepcopy(p)}
                last = _result(accepted=True, code="WORK_COMPLETED_WITH_NO_RESULT", state_changed=True, work_state="NO_RESULT")

        elif kind == "ASSERT_WORKER_AUTHORITY":
            last = _result(code="WORKER_AUTHORITY_FORBIDDEN", work_state=state_of(wid, accepted, started, terminal))
        else:
            last = _result(code="UNKNOWN_OPERATION", work_state=state_of(wid, accepted, started, terminal))

    return deepcopy(last)
