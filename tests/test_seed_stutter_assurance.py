from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def profile() -> dict:
    return json.loads(
        (ROOT / "assurance/seed-stutter/ASSURANCE_PROFILE.json").read_text(
            encoding="utf-8"
        )
    )


def test_profile_is_non_normative_evidence_composition() -> None:
    value = profile()
    assert value["normative"] is False
    assert value["normative_precedence"] == "NONE"
    assert value["relation_type"] == "EVIDENCE_COMPOSITION_OVER_SHARED_SEED_SUBJECT"


def test_profile_pins_public_v60_and_exact_seed_subject() -> None:
    value = profile()
    assert (
        value["public_v60_subject"]["commit"]
        == "e89d984203a126f8bc62467224cdf6c5374dada7"
    )
    assert value["public_v60_subject"]["expected_tlaps_obligations"] == 2257
    assert value["shared_seed_subject"]["seed_resolution_sha256"] == (
        "sha256:1c0ebb27ed52da289f0981dcb11b61b6a7fc5c4a030ba434ae0b1d53b286b926"
    )


def test_profile_does_not_claim_new_composed_theorem() -> None:
    assert (
        "a new mechanically composed Worker-to-v60 TLAPS theorem"
        in profile()["claim_boundary"]["excluded"]
    )


def test_worker_projection_contract_remains_non_authoritative() -> None:
    contract = profile()["projection_contract"]
    assert contract["worker_operations"] == "SEED_STUTTER"
    assert contract["worker_owned_seed_state"] is False
    assert contract["worker_creates_seed_resolution"] is False
    assert contract["worker_grants_external_effect_permission"] is False
