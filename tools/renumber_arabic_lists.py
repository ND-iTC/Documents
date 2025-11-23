import re
import sys
from pathlib import Path

"""
Simplified renumbering for ND SD-style docs.

Behavior:
- Maintain ONE global counter for top-level numbered items.
- Only two things matter:
    1) [arabic] / [arabic, start=N] lines
    2) lines starting with ". " (dot + space)

- For each [arabic] block, we:
    - Look ahead and count how many ". " lines belong to it,
      stopping at the next [arabic...] or a heading.
    - Set its start value so numbering continues from the
      previous block (no overlaps, no gaps unless you make them).

- We IGNORE:
    - ".." nested items (they are local, not part of global count)
    - [loweralpha], [upperalpha], etc.
    - bullets (*, -)
    - attribute blocks, notes, pseudocode, etc.

This lets you:
- Have global numbering for main eval activities.
- Also have nested lettered/numbered lists inside,
  without them messing up the global sequence.

Usage:
    python3 renumber_arabic_lists_simple.py ND_Supporting_Document_4_0-draft.adoc
"""

if len(sys.argv) < 2:
    print("Usage: renumber_arabic_lists_simple.py <file.adoc>")
    sys.exit(1)

path = Path(sys.argv[1])
text = path.read_text(encoding="utf-8", errors="ignore")
lines = text.splitlines()

current_number = 0  # last assigned top-level number


def is_arabic_attr(line: str):
    """Return True if line is [arabic] or [arabic, start=N]."""
    return re.match(r'^\[arabic(?:\s*,\s*start\s*=\s*\d+)?\]\s*$', line.strip()) is not None


def is_heading(line: str):
    s = line.strip()
    # AsciiDoc heading like "=== Title"
    if re.match(r'^(=+)\s+\S', s):
        return True
    # Numbered clause heading like "3.3.1.3. Tests"
    if re.match(r'^\d+(\.\d+)*\.\s', s):
        return True
    return False


i = 0
n = len(lines)

while i < n:
    line = lines[i]

    if not is_arabic_attr(line):
        i += 1
        continue

    # We found a [arabic...] block.
    j = i + 1
    count = 0

    while j < n:
        l = lines[j]
        s = l.strip()

        # Stop this block when we hit:
        # - the next [arabic...] (start of new block), or
        # - a heading.
        if is_arabic_attr(l) and j != i:
            break
        if is_heading(l):
            break

        # Only count top-level ". " lines as items.
        if re.match(r'^\.\s+', l):
            count += 1

        j += 1

    # If this [arabic] has items, assign its start.
    if count > 0:
        start = current_number + 1 if current_number > 0 else 1
        if start == 1:
            lines[i] = "[arabic]"
        else:
            lines[i] = f"[arabic, start={start}]"
        current_number = start + count - 1
    # If count == 0, we leave it alone (likely a malformed or special block).

    i = j

# Write updated file
path.write_text("\n".join(lines), encoding="utf-8")
print(f"Renumbered [arabic] blocks based on '. ' items in: {path}")
