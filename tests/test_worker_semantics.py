import json
from pathlib import Path
from reference.oracle import run_case

ROOT = Path(__file__).resolve().parents[1]


def test_all_conformance_cases():
    for p in sorted((ROOT / "extension/canonical/conformance/cases").rglob("*.json")):
        case = json.loads(p.read_text())
        assert run_case(case) == case["expected"]


def test_terminal_pair_is_xor_in_canon():
    model = json.loads((ROOT / "extension/canonical/source/worker-model.json").read_text())
    assert model["state_machine"]["terminal_states"] == ["RESULT", "NO_RESULT"]
    assert model["state_machine"]["terminal_relation"] == "XOR"


def test_no_result_is_explicit_not_absence():
    model = json.loads((ROOT / "extension/canonical/source/worker-model.json").read_text())
    assert "explicit terminal assertion" in model["derived_semantics"]["NO_RESULT_NOT_ABSENCE"]


def test_worker_does_not_claim_authority():
    model = json.loads((ROOT / "extension/canonical/source/worker-model.json").read_text())
    texts = " ".join(x["text"] for x in model["requirements"] + model["invariants"])
    assert "Authority" in texts
    assert "Seed Resolution" in texts


def test_acceptance_is_not_in_worker_lifecycle():
    model = json.loads((ROOT / "extension/canonical/source/worker-model.json").read_text())
    assert [x["kind"] for x in model["operations"]] == ["START_WORK", "END_WORK"]
    assert "ACCEPTED" not in model["state_machine"]["stored_or_derived_states"]
    assert "eligibility, assignment or acceptance" in model["normative_scope"]["does_not_define"]


def test_work_descriptor_is_opaque_to_worker():
    model = json.loads((ROOT / "extension/canonical/source/worker-model.json").read_text())
    text = model["semantic_objects"]["work_descriptor_binding"]
    assert "Opaque" in text
    assert "does not interpret" in text
