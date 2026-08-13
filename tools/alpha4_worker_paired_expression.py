from __future__ import annotations

import itertools
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FORTH = ROOT / "worker/alpha4/operational/components.forth"
RELATIONAL = ROOT / "worker/alpha4/formal/WorkerRelations.tla"

EXPECTED_WORDS = {
    "START-MISSING": ("EXACT-START?", "0=", "KEEP-WORK", "WORK-BINDING-REQUIRED"),
    "START-FRESH": ("EXACT-START?", "FRESH-WORK-ID?", "ADD-START", "WORK-STARTED"),
    "START-REPLAY": (
        "EXACT-START?",
        "EXACT-START-REPLAY?",
        "KEEP-WORK",
        "IDEMPOTENT-REPLAY",
    ),
    "START-CONFLICT": (
        "EXACT-START?",
        "CONFLICTING-WORK-ID?",
        "KEEP-WORK",
        "WORK-IDENTITY-CONFLICT",
    ),
    "END-NOT-STARTED": ("WORK-STARTED?", "0=", "KEEP-WORK", "WORK-NOT-STARTED"),
    "END-BINDING-MISMATCH": (
        "WORK-STARTED?",
        "START-BINDING-MATCH?",
        "0=",
        "KEEP-WORK",
        "WORK-BINDING-MISMATCH",
    ),
    "END-KIND-REQUIRED": (
        "WORK-STARTED?",
        "START-BINDING-MATCH?",
        "TERMINAL-KIND?",
        "0=",
        "KEEP-WORK",
        "TERMINAL-KIND-REQUIRED",
    ),
    "END-BINDING-REQUIRED": (
        "WORK-STARTED?",
        "START-BINDING-MATCH?",
        "TERMINAL-KIND?",
        "EXACT-TERMINAL?",
        "0=",
        "KEEP-WORK",
        "TERMINAL-BINDING-REQUIRED",
    ),
    "END-RESULT": (
        "EXACT-END?",
        "RUNNING-WORK?",
        "RESULT?",
        "ADD-TERMINAL",
        "WORK-ENDED-WITH-RESULT",
    ),
    "END-NO-RESULT": (
        "EXACT-END?",
        "RUNNING-WORK?",
        "NO-RESULT?",
        "ADD-TERMINAL",
        "WORK-ENDED-WITH-NO-RESULT",
    ),
    "END-REPLAY": (
        "EXACT-END?",
        "EXACT-TERMINAL-REPLAY?",
        "KEEP-WORK",
        "IDEMPOTENT-REPLAY",
    ),
    "END-CONFLICT": (
        "EXACT-END?",
        "TERMINAL-EXISTS?",
        "CONFLICTING-TERMINAL?",
        "KEEP-WORK",
        "TERMINAL-WORK-IMMUTABLE",
    ),
}

START_FIELDS = {
    "work_id",
    "work_binding_digest",
    "worker_binding",
    "work_descriptor_binding",
}
END_FIELDS = {
    "work_id",
    "work_binding_digest",
    "terminal_kind",
    "terminal_record_digest",
    "terminal_binding",
    "evidence_bindings",
}


def parse_operational_words() -> dict[str, tuple[str, ...]]:
    text = FORTH.read_text(encoding="utf-8")
    pattern = re.compile(r":\s+(?P<word>[A-Z0-9-]+)\s+\([^)]*--[^)]*\)\s+(?P<body>.*?)\s*;")
    words = {m.group("word"): tuple(m.group("body").split()) for m in pattern.finditer(text)}
    if words != EXPECTED_WORDS:
        raise RuntimeError(f"restricted Worker vocabulary mismatch: {words!r}")
    return words


def validate_relational_surface() -> None:
    text = RELATIONAL.read_text(encoding="utf-8")
    required = {
        "StartMissing": "WORK_BINDING_REQUIRED",
        "StartFresh": "WORK_STARTED",
        "StartReplay": "IDEMPOTENT_REPLAY",
        "StartConflict": "WORK_IDENTITY_CONFLICT",
        "EndNotStarted": "WORK_NOT_STARTED",
        "EndBindingMismatch": "WORK_BINDING_MISMATCH",
        "EndKindRequired": "TERMINAL_KIND_REQUIRED",
        "EndBindingRequired": "TERMINAL_BINDING_REQUIRED",
        "EndResult": "WORK_ENDED_WITH_RESULT",
        "EndNoResult": "WORK_ENDED_WITH_NO_RESULT",
        "EndReplay": "IDEMPOTENT_REPLAY",
        "EndConflict": "TERMINAL_WORK_IMMUTABLE",
    }
    for operator, result in required.items():
        match = re.search(rf"(?ms)^{operator}\(.*?^\s*/\\ result = \"([^\"]+)\"", text)
        if match is None or match.group(1) != result:
            raise RuntimeError(f"relational branch drift: {operator}")


def exact_start(request: dict[str, Any]) -> bool:
    return set(request) == START_FIELDS and all(request.get(field) for field in START_FIELDS)


def exact_end(request: dict[str, Any]) -> bool:
    return (
        set(request) == END_FIELDS
        and bool(request.get("work_id"))
        and bool(request.get("work_binding_digest"))
        and request.get("terminal_kind") in {"RESULT", "NO_RESULT"}
        and bool(request.get("terminal_record_digest"))
        and bool(request.get("terminal_binding"))
    )


def empty_state() -> dict[str, list[dict[str, Any]]]:
    return {"started": [], "terminals": []}


def _starts_for(state: dict[str, Any], work_id: str | None) -> list[dict[str, Any]]:
    return [x for x in state["started"] if x["work_id"] == work_id]


def _terminals_for(state: dict[str, Any], work_id: str | None) -> list[dict[str, Any]]:
    return [x for x in state["terminals"] if x["work_id"] == work_id]


def _result(branch: str, code: str, recognized: bool, changed: bool) -> dict[str, Any]:
    return {
        "branch": branch,
        "code": code,
        "recognized": recognized,
        "state_changed": changed,
        "authority_created": False,
        "effect_permitted": False,
        "seed_projection": "STUTTER",
    }


def operational_start(
    state: dict[str, Any], request: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_operational_words()
    if not exact_start(request):
        return deepcopy(state), _result("START-MISSING", "WORK_BINDING_REQUIRED", False, False)
    same_id = _starts_for(state, request["work_id"])
    if not same_id:
        out = deepcopy(state)
        out["started"].append(deepcopy(request))
        return out, _result("START-FRESH", "WORK_STARTED", True, True)
    if request in same_id:
        return deepcopy(state), _result("START-REPLAY", "IDEMPOTENT_REPLAY", True, False)
    return deepcopy(state), _result("START-CONFLICT", "WORK_IDENTITY_CONFLICT", False, False)


def relational_start(
    state: dict[str, Any], request: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    if set(request) != START_FIELDS or not all(request.get(field) for field in START_FIELDS):
        return deepcopy(state), _result("START-MISSING", "WORK_BINDING_REQUIRED", False, False)
    identical = request in state["started"]
    identifier_exists = any(x["work_id"] == request["work_id"] for x in state["started"])
    if identical:
        return deepcopy(state), _result("START-REPLAY", "IDEMPOTENT_REPLAY", True, False)
    if identifier_exists:
        return deepcopy(state), _result("START-CONFLICT", "WORK_IDENTITY_CONFLICT", False, False)
    out = deepcopy(state)
    out["started"].append(deepcopy(request))
    return out, _result("START-FRESH", "WORK_STARTED", True, True)


def _matching_start(state: dict[str, Any], request: dict[str, Any]) -> dict[str, Any] | None:
    starts = _starts_for(state, request.get("work_id"))
    return starts[0] if starts else None


def operational_end(
    state: dict[str, Any], request: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    parse_operational_words()
    start = _matching_start(state, request)
    if start is None:
        return deepcopy(state), _result("END-NOT-STARTED", "WORK_NOT_STARTED", False, False)
    if request.get("work_binding_digest") != start["work_binding_digest"]:
        return deepcopy(state), _result(
            "END-BINDING-MISMATCH", "WORK_BINDING_MISMATCH", False, False
        )
    if request.get("terminal_kind") not in {"RESULT", "NO_RESULT"}:
        return deepcopy(state), _result("END-KIND-REQUIRED", "TERMINAL_KIND_REQUIRED", False, False)
    if not request.get("terminal_record_digest") or not request.get("terminal_binding"):
        return deepcopy(state), _result(
            "END-BINDING-REQUIRED", "TERMINAL_BINDING_REQUIRED", False, False
        )
    previous = _terminals_for(state, request.get("work_id"))
    if previous:
        if request in previous:
            return deepcopy(state), _result("END-REPLAY", "IDEMPOTENT_REPLAY", True, False)
        return deepcopy(state), _result("END-CONFLICT", "TERMINAL_WORK_IMMUTABLE", False, False)
    out = deepcopy(state)
    out["terminals"].append(deepcopy(request))
    if request["terminal_kind"] == "RESULT":
        return out, _result("END-RESULT", "WORK_ENDED_WITH_RESULT", True, True)
    return out, _result("END-NO-RESULT", "WORK_ENDED_WITH_NO_RESULT", True, True)


def relational_end(
    state: dict[str, Any], request: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    start = _matching_start(state, request)
    if start is None:
        return deepcopy(state), _result("END-NOT-STARTED", "WORK_NOT_STARTED", False, False)
    if request.get("work_binding_digest") != start["work_binding_digest"]:
        return deepcopy(state), _result(
            "END-BINDING-MISMATCH", "WORK_BINDING_MISMATCH", False, False
        )
    if request.get("terminal_kind") not in {"RESULT", "NO_RESULT"}:
        return deepcopy(state), _result("END-KIND-REQUIRED", "TERMINAL_KIND_REQUIRED", False, False)
    if not request.get("terminal_record_digest") or not request.get("terminal_binding"):
        return deepcopy(state), _result(
            "END-BINDING-REQUIRED", "TERMINAL_BINDING_REQUIRED", False, False
        )
    identical = request in state["terminals"]
    terminal_exists = any(x["work_id"] == request["work_id"] for x in state["terminals"])
    if identical:
        return deepcopy(state), _result("END-REPLAY", "IDEMPOTENT_REPLAY", True, False)
    if terminal_exists:
        return deepcopy(state), _result("END-CONFLICT", "TERMINAL_WORK_IMMUTABLE", False, False)
    out = deepcopy(state)
    out["terminals"].append(deepcopy(request))
    if request["terminal_kind"] == "RESULT":
        return out, _result("END-RESULT", "WORK_ENDED_WITH_RESULT", True, True)
    return out, _result("END-NO-RESULT", "WORK_ENDED_WITH_NO_RESULT", True, True)


def _start(work_id: str, digest: str, worker: str, descriptor: str) -> dict[str, str]:
    return {
        "work_id": work_id,
        "work_binding_digest": digest,
        "worker_binding": worker,
        "work_descriptor_binding": descriptor,
    }


def _end(
    work_id: str,
    digest: str,
    kind: str | None,
    record: str | None,
    binding: str | None,
    evidence: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    return {
        "work_id": work_id,
        "work_binding_digest": digest,
        "terminal_kind": kind,
        "terminal_record_digest": record,
        "terminal_binding": binding,
        "evidence_bindings": evidence,
    }


def bounded_pairing_check() -> tuple[int, dict[str, int]]:
    validate_relational_surface()
    parse_operational_words()
    digests = ["sha256:" + ch * 64 for ch in ("1", "2")]
    starts = [
        _start(wid, digest, worker, descriptor)
        for wid, digest, worker, descriptor in itertools.product(
            ("work:0", "work:1"), digests, ("worker:0", "worker:1"), ("desc:0", "desc:1")
        )
    ]
    missing_start = deepcopy(starts[0])
    missing_start["work_binding_digest"] = ""
    start_requests = [*starts, missing_start]

    base_start = starts[0]
    terminal_result = _end(
        base_start["work_id"],
        base_start["work_binding_digest"],
        "RESULT",
        "record:0",
        "term:0",
    )
    terminal_no_result = _end(
        base_start["work_id"],
        base_start["work_binding_digest"],
        "NO_RESULT",
        "record:1",
        "term:1",
    )
    states = [empty_state(), {"started": [deepcopy(base_start)], "terminals": []}]
    states.extend(
        [
            {"started": [deepcopy(base_start)], "terminals": [deepcopy(terminal_result)]},
            {"started": [deepcopy(base_start)], "terminals": [deepcopy(terminal_no_result)]},
        ]
    )
    end_requests = [
        terminal_result,
        terminal_no_result,
        _end("work:1", digests[0], "RESULT", "record:0", "term:0"),
        _end(base_start["work_id"], digests[1], "RESULT", "record:0", "term:0"),
        _end(base_start["work_id"], base_start["work_binding_digest"], None, "record:0", "term:0"),
        _end(base_start["work_id"], base_start["work_binding_digest"], "RESULT", None, None),
        _end(
            base_start["work_id"],
            base_start["work_binding_digest"],
            "NO_RESULT",
            "record:x",
            "term:x",
        ),
    ]
    checks = 0
    branches = {name: 0 for name in EXPECTED_WORDS}
    for state in states:
        for request in start_requests:
            op_state, op_result = operational_start(state, request)
            rel_state, rel_result = relational_start(state, request)
            if op_state != rel_state or op_result != rel_result:
                raise RuntimeError(f"start pairing mismatch: {state!r} {request!r}")
            branches[op_result["branch"]] += 1
            if op_result["authority_created"] or op_result["effect_permitted"]:
                raise RuntimeError("Worker transition crossed Seed authority boundary")
            if op_result["seed_projection"] != "STUTTER":
                raise RuntimeError("Worker transition is not a Seed stutter")
            checks += 1
        for request in end_requests:
            op_state, op_result = operational_end(state, request)
            rel_state, rel_result = relational_end(state, request)
            if op_state != rel_state or op_result != rel_result:
                raise RuntimeError(f"end pairing mismatch: {state!r} {request!r}")
            branches[op_result["branch"]] += 1
            if op_result["authority_created"] or op_result["effect_permitted"]:
                raise RuntimeError("Worker transition crossed Seed authority boundary")
            if op_result["seed_projection"] != "STUTTER":
                raise RuntimeError("Worker transition is not a Seed stutter")
            checks += 1
    missing = sorted(name for name, count in branches.items() if count == 0)
    if missing:
        raise RuntimeError(f"uncovered Worker branches: {missing}")
    return checks, branches


def main() -> int:
    checks, branches = bounded_pairing_check()
    print("ALPHA4_WORKER_OPERATIONAL_WORDS=12/12 PASS")
    print(f"ALPHA4_WORKER_PAIRED_CASES={checks}/{checks} PASS")
    branch_summary = ",".join(f"{name}:{branches[name]}" for name in sorted(branches))
    print("ALPHA4_WORKER_BRANCH_COVERAGE=" + branch_summary)
    print("ALPHA4_WORKER_SEED_PROJECTION=STUTTER")
    print("ALPHA4_WORKER_PAIRED_EXPRESSION=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
