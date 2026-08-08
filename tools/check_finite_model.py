from __future__ import annotations
from collections import deque
from dataclasses import dataclass

WORKS = ("w1", "w2")

@dataclass(frozen=True)
class State:
    accepted: frozenset[str]
    started: frozenset[str]
    result: frozenset[str]
    no_result: frozenset[str]

INIT = State(frozenset(), frozenset(), frozenset(), frozenset())


def invariant(s: State) -> None:
    U = frozenset(WORKS)
    assert s.accepted <= U
    assert s.started <= s.accepted
    assert s.result <= s.started
    assert s.no_result <= s.started
    assert not (s.result & s.no_result)


def successors(s: State):
    terminal = s.result | s.no_result
    for w in WORKS:
        if w not in s.accepted:
            yield ("ACCEPT_WORK", w), State(s.accepted | {w}, s.started, s.result, s.no_result)
        if w in s.accepted and w not in s.started and w not in terminal:
            yield ("START_WORK", w), State(s.accepted, s.started | {w}, s.result, s.no_result)
        if w in s.started and w not in terminal:
            yield ("COMPLETE_WITH_RESULT", w), State(s.accepted, s.started, s.result | {w}, s.no_result)
            yield ("COMPLETE_WITH_NO_RESULT", w), State(s.accepted, s.started, s.result, s.no_result | {w})


def state_of(s: State, w: str) -> str:
    if w not in s.accepted:
        return "UNREGISTERED"
    if w in s.result:
        return "RESULT"
    if w in s.no_result:
        return "NO_RESULT"
    if w in s.started:
        return "RUNNING"
    return "ACCEPTED"


def main():
    q = deque([INIT])
    seen = {INIT}
    edges = 0
    observed_states = set()
    while q:
        s = q.popleft()
        invariant(s)
        for w in WORKS:
            observed_states.add(state_of(s, w))
        for _, nxt in successors(s):
            invariant(nxt)
            edges += 1
            if nxt not in seen:
                seen.add(nxt)
                q.append(nxt)
    expected = {"UNREGISTERED", "ACCEPTED", "RUNNING", "RESULT", "NO_RESULT"}
    assert observed_states == expected, (observed_states, expected)
    print(f"FINITE_MODEL_REACHABLE_STATES={len(seen)}")
    print(f"FINITE_MODEL_EDGES={edges}")
    print("FINITE_MODEL_LIFECYCLE_STATES=" + ",".join(sorted(observed_states)))
    print("FINITE_MODEL_RESULT_XOR_NO_RESULT=PASS")
    print("FINITE_MODEL_GATE=PASS")

if __name__ == '__main__':
    main()
