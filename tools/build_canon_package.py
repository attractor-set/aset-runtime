from __future__ import annotations
import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANON = ROOT / 'extension/canonical'
PACKAGE = CANON / 'CANON_PACKAGE.json'

ROLES = {
    'source/worker-model.json':'NORMATIVE_MACHINE_CANON',
    'protocol/protocol-profile.json':'NORMATIVE_PROTOCOL_PROFILE',
    'protocol/schemas/accept-work.schema.json':'NORMATIVE_WIRE_SCHEMA',
    'protocol/schemas/start-work.schema.json':'NORMATIVE_WIRE_SCHEMA',
    'protocol/schemas/complete-with-result.schema.json':'NORMATIVE_WIRE_SCHEMA',
    'protocol/schemas/complete-with-no-result.schema.json':'NORMATIVE_WIRE_SCHEMA',
    'protocol/schemas/conformance-case.schema.json':'NORMATIVE_CONFORMANCE_SCHEMA',
    'protocol/schemas/worker-model.schema.json':'NORMATIVE_CANON_SCHEMA',
    'conformance/conformance-profile.json':'NORMATIVE_CONFORMANCE_PROFILE',
}
for p in sorted((CANON/'conformance/cases').rglob('*.json')):
    ROLES[p.relative_to(CANON).as_posix()] = 'NORMATIVE_CONFORMANCE_CASE'
for rel in [
    'formal/WorkerLifecycle.tla',
    'formal/WorkerLifecycle.cfg',
    'formal/WorkerLifecycleProofs.tla',
    'formal/WorkerCanonProjection.tla',
    'formal/WorkerCanonRefinementProofs.tla',
    'formal/WorkerSeedStuttering.tla',
    'formal/WorkerSeedStutteringProofs.tla',
    'formal/README.md',
    'assurance/canon-tla-refinement.json',
    'assurance/seed-refinement.json',
    'assurance/lifecycle-proof-candidate.json',
    'assurance/lifecycle-proof.json',
    'assurance/canon-refinement-proof.json',
    'assurance/seed-refinement-proof.json',
    'assurance/verification-registry.json',
]:
    ROLES[rel] = 'NON_NORMATIVE_ASSURANCE_ARTIFACT'


def digest(p):
    return 'sha256:' + hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    files=[]
    for rel, role in sorted(ROLES.items()):
        p=CANON/rel
        files.append({'path':rel,'role':role,'sha256':digest(p)})
    payload={
        'document_type':'aset-worker-canon-package','schema_version':1,
        'canon_id':'ASET-WORKER-CANON-0.1-ALPHA1','version':'0.1.0-alpha.0','files':files
    }
    PACKAGE.write_text(json.dumps(payload, indent=2, sort_keys=True)+'\n')
    print(f"CANON_PACKAGE_FILES={len(files)}")
    print("CANON_PACKAGE_BUILD=PASS")

if __name__ == '__main__':
    main()
