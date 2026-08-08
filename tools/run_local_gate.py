from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(rel):
    p = subprocess.run([sys.executable, str(ROOT / rel)], cwd=ROOT, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"gate failed: {rel} -> {p.returncode}")


def structural_checks():
    model=json.loads((ROOT/'extension/canonical/source/worker-model.json').read_text())
    binding=json.loads((ROOT/'upstream/ASET_SEED_BINDING.json').read_text())
    assert model['canon_id']=='ASET-WORKER-CANON-0.1-ALPHA1'
    assert model['state_machine']['terminal_states']==['RESULT','NO_RESULT']
    assert model['state_machine']['terminal_relation']=='XOR'
    assert [x['kind'] for x in model['operations']]==['ACCEPT_WORK','START_WORK','COMPLETE_WITH_RESULT','COMPLETE_WITH_NO_RESULT']
    assert len(model['requirements'])==11
    assert len(model['invariants'])==11
    assert binding['compatibility_standard']=='ASET-SEED-COMPATIBILITY-STANDARD@seed-0.3.0-alpha.3'
    assert binding['seed_release_commit']=='633c130187b2a2bb42f24cfd66662d475de385d2'
    assert model['formal_assurance']['canon_to_tla_equivalence']=='OPEN'
    assert model['formal_assurance']['seed_refinement']=='OPEN'
    text=(ROOT/'README.md').read_text()
    assert 'NO_RESULT' in text and 'RESULT' in text and 'XOR' in text
    print('STRUCTURAL_CANON_CHECKS=PASS')
    print('UPSTREAM_SEED_BINDING=PASS')
    print('FORMAL_CLAIM_BOUNDARY=PASS')


def main():
    print('=== ASET WORKER LOCAL GATE ===')
    structural_checks()
    run('tools/verify_formal_candidate.py')
    run('tools/verify_canon_package.py')
    run('tools/run_conformance.py')
    run('tools/check_finite_model.py')
    registry_path = ROOT/'extension/canonical/assurance/verification-registry.json'
    if registry_path.is_file():
        registry=json.loads(registry_path.read_text())
        if registry.get('status') == 'MECHANICALLY_PROVED':
            proofs={p['id']:p for p in registry.get('proofs', [])}
            print(f"MATERIALIZED_TLAPS_SAFETY={proofs.get('WORKER_TLAPS_SAFETY',{}).get('status','UNKNOWN')}")
            print(f"MATERIALIZED_CANON_TO_TLA={proofs.get('WORKER_CANON_TO_TLA',{}).get('status','UNKNOWN')}")
            print(f"MATERIALIZED_SEED_REFINEMENT={proofs.get('WORKER_SEED_REFINEMENT',{}).get('status','UNKNOWN')}")
            print('FORMAL_RELEASE_GATE=REQUIRES_REPRODUCIBLE_FORMAL_RELEASE_GATE')
        else:
            print('FORMAL_RELEASE_GATE=BLOCKED')
    else:
        print('CANON_TO_TLA=OPEN')
        print('TLAPS_SAFETY=OPEN')
        print('SEED_REFINEMENT=OPEN')
        print('FORMAL_RELEASE_GATE=BLOCKED')
    print('ASET_WORKER_LOCAL_GATE=PASS')

if __name__=='__main__':
    main()
