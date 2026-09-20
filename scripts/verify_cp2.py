import csv
import re
from pathlib import Path

D = Path('data/ecommerce')
REQ = ['doc_id', 'title', 'source_url', 'retrieved_at', 'document_version', 'audience']
mds = sorted(D.glob('*.md'))
rows = list(csv.DictReader(open(D / 'sources.csv', encoding='utf-8')))

ids, auds = [], {}
for p in mds:
    content = p.read_text(encoding='utf-8')
    fm_text = content.split('---')[1]
    fm = dict(re.findall(r'^(\w+):\s*(.+)$', fm_text, re.M))
    
    # Strip quotes if present
    for k, v in fm.items():
        fm[k] = v.strip('"\'')
        
    doc_id = fm.get('doc_id')
    audience = fm.get('audience')
    ids.append(doc_id)
    auds[audience] = auds.get(audience, 0) + 1
    
    is_ok = all(k in fm for k in REQ) and doc_id == p.stem
    status = "OK" if is_ok else "THIEU METADATA"
    print(f'{p.name:40} {status}')

print('so file :', len(mds), '(can 5-10)')
csv_match = 'khop' if sorted(r['doc_id'] for r in rows) == sorted(ids) else 'LECH'
print('csv     :', csv_match)
print('audience:', auds)
