"""One-off patch: make agents/aggregate.py understand 'lakh crore' (= 1 trillion).

Run from the project folder:
    python patch_lakh_crore.py
Safe to re-run: it stops if a target line is missing or already patched.
A backup is saved as agents/aggregate.py.bak
"""
from pathlib import Path
import shutil

path = Path("agents/aggregate.py")
raw = path.read_bytes()
text = raw.decode("utf-8")

edits = [
    # 1. unit table: 1 lakh crore = 1e12 = 1000 billion
    ('"crore": 1e-2, "lakh": 1e-4}',
     '"crore": 1e-2, "lakh": 1e-4, "lakh crore": 1000.0}'),
    # 2. regex: try the two-word unit first so 'lakh crore' is not read as 'lakh'
    ('(?P<unit>trillion|billion|million|thousand|crore|lakh)',
     '(?P<unit>lakh\\s+crore|trillion|billion|million|thousand|crore|lakh)'),
    # 3. normalise spacing in the matched unit
    ('unit = match.group("unit").lower()',
     'unit = " ".join(match.group("unit").lower().split())'),
    # 4. tell the model it may answer 'lakh crore'
    ('crore, lakh, trillion, percent,',
     'crore, lakh, lakh crore, trillion, percent,'),
]

for old, new in edits:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"STOPPED: expected 1 match, found {n} for: {old!r}")
    text = text.replace(old, new)

shutil.copyfile(path, "agents/aggregate.py.bak")
path.write_bytes(text.encode("utf-8"))
print("Patched agents/aggregate.py (backup: agents/aggregate.py.bak)")
