"""Refresh only the reviewed draft contract/instrument lock; never recapture sources.

Use after editing the P1 draft. check-baseline.sh never calls this builder. Any
source drift still fails against the unchanged frozen baseline observations.
"""
from baseline_io import BASE, ROOT, dump, fingerprint, load


def refresh():
    paths = [*list((BASE / 'contracts/v1').glob('*.json')), *list((BASE / 'fixtures/v1').glob('*.json')),
        *[BASE / x for x in ['tools-v1.json', 'pi-inputs-v1.json', 'locations.json', 'approval-source.json',
                            'redirects-m1c.json', 'disagreements.json', 'CONTRACTS.md']],
        *list((ROOT / 'scripts/fp').glob('*.py')), ROOT / 'scripts/fp/check-baseline.sh',
        ROOT / 'scripts/fp/requirements.txt', ROOT / 'tests/test_fp_baseline.py', ROOT / '.gitignore']
    dump(BASE / 'contracts-lock.json', {'schema_version': 'mind/contracts-lock@1', 'artifacts': [
         {'location': {'backend': 'repo', 'path': str(path.relative_to(ROOT))}, **fingerprint(path)} for path in sorted(paths)]})
    release = load(BASE / 'tested-release-v10.json')
    for field, path in [('baseline', BASE / 'baseline.json'), ('contract_inventory', BASE / 'contracts-lock.json')]:
        release[field] = {'location': {'backend': 'repo', 'path': str(path.relative_to(ROOT))}, **fingerprint(path)}
    updates = {str(path.relative_to(ROOT)): fingerprint(path) for path in [BASE / 'baseline.json', BASE / 'contracts-lock.json']}
    def update_refs(value):
        if isinstance(value, dict):
            location = value.get('location', {})
            if location.get('backend') == 'repo' and location.get('path') in updates:
                value.update(updates[location['path']])
            for child in value.values():
                update_refs(child)
        elif isinstance(value, list):
            for child in value:
                update_refs(child)
    update_refs(release)
    dump(BASE / 'tested-release-v10.json', release)
    print('Refreshed draft contract lock; frozen source observations were not recaptured.')


if __name__ == '__main__':
    refresh()
