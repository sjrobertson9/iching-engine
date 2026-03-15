"""
I Ching Casting Engine
Three-coin method using SHA-256 whitened Claude conversation history
Sums: 6 = old yin (changing), 7 = young yang, 8 = young yin, 9 = old yang (changing)
"""

import hashlib

# ── PIPELINE ──────────────────────────────────────────────────────────────────

def load_bits(path="all_digits.txt"):
    with open(path, "r") as f:
        raw = f.read()
    digit_str = "".join(c for c in raw if c.isdigit())
    bits = []
    chunk_size = 64
    for i in range(0, len(digit_str) - chunk_size, chunk_size):
        chunk = digit_str[i:i+chunk_size].encode()
        hash_bytes = hashlib.sha256(chunk).digest()
        for byte in hash_bytes:
            for bit_pos in range(8):
                bits.append((byte >> (7 - bit_pos)) & 1)
    return bits

# ── CASTING ───────────────────────────────────────────────────────────────────

bit_index = 0
bits = []

def flip_coin():
    global bit_index
    if bit_index >= len(bits):
        bit_index = 0
    result = bits[bit_index]
    bit_index += 1
    return 3 if result == 1 else 2  # heads=3, tails=2

def cast_line():
    """Flip three coins, return (sum, line_type, symbol)"""
    total = flip_coin() + flip_coin() + flip_coin()
    if total == 6:
        return total, "old yin",  "-- x --"   # changing yin
    elif total == 7:
        return total, "young yang", "-----"   # stable yang
    elif total == 8:
        return total, "young yin",  "-- --"   # stable yin
    elif total == 9:
        return total, "old yang",  "--o--"    # changing yang

def cast_hexagram():
    """Cast six lines bottom to top, return lines and whether there are changes."""
    lines = []
    for _ in range(6):
        lines.append(cast_line())
    return lines

def lines_to_number(lines):
    """Convert 6 lines to hexagram number (1-64) using verified King Wen sequence."""
    # Identify trigram name from three lines (bottom to top)
    # yang=solid, yin=broken
    def trigram_name(l1, l2, l3):  # l1=bottom, l3=top
        y = tuple(1 if x in (7, 9) else 0 for x in (l1, l2, l3))
        names = {
            (1,1,1):'Qian', (0,0,0):'Kun',  (0,0,1):'Zhen', (1,1,0):'Xun',
            (0,1,0):'Kan',  (1,0,1):'Li',   (1,0,0):'Gen',  (0,1,1):'Dui',
        }
        return names[y]

    t = [total for total, _, _ in lines]
    upper = trigram_name(t[3], t[4], t[5])
    lower = trigram_name(t[0], t[1], t[2])

    # Verified King Wen sequence (upper, lower) → hexagram number
    king_wen = {
        ('Qian','Qian'):1,  ('Qian','Kun'):12, ('Qian','Zhen'):25, ('Qian','Xun'):44,
        ('Qian','Kan'):6,   ('Qian','Li'):13,  ('Qian','Gen'):33,  ('Qian','Dui'):10,
        ('Kun','Qian'):11,  ('Kun','Kun'):2,   ('Kun','Zhen'):24,  ('Kun','Xun'):46,
        ('Kun','Kan'):7,    ('Kun','Li'):36,   ('Kun','Gen'):15,   ('Kun','Dui'):19,
        ('Zhen','Qian'):34, ('Zhen','Kun'):16, ('Zhen','Zhen'):51, ('Zhen','Xun'):32,
        ('Zhen','Kan'):40,  ('Zhen','Li'):55,  ('Zhen','Gen'):62,  ('Zhen','Dui'):54,
        ('Xun','Qian'):9,   ('Xun','Kun'):20,  ('Xun','Zhen'):42,  ('Xun','Xun'):57,
        ('Xun','Kan'):59,   ('Xun','Li'):37,   ('Xun','Gen'):53,   ('Xun','Dui'):61,
        ('Kan','Qian'):5,   ('Kan','Kun'):8,   ('Kan','Zhen'):3,   ('Kan','Xun'):48,
        ('Kan','Kan'):29,   ('Kan','Li'):63,   ('Kan','Gen'):39,   ('Kan','Dui'):60,
        ('Li','Qian'):14,   ('Li','Kun'):35,   ('Li','Zhen'):21,   ('Li','Xun'):50,
        ('Li','Kan'):64,    ('Li','Li'):30,    ('Li','Gen'):56,    ('Li','Dui'):38,
        ('Gen','Qian'):26,  ('Gen','Kun'):23,  ('Gen','Zhen'):27,  ('Gen','Xun'):18,
        ('Gen','Kan'):4,    ('Gen','Li'):22,   ('Gen','Gen'):52,   ('Gen','Dui'):41,
        ('Dui','Qian'):43,  ('Dui','Kun'):45,  ('Dui','Zhen'):17,  ('Dui','Xun'):28,
        ('Dui','Kan'):47,   ('Dui','Li'):49,   ('Dui','Gen'):31,   ('Dui','Dui'):58,
    }
    return king_wen[(upper, lower)]

def changing_lines_to_number(lines):
    """Flip changing lines to get the second hexagram."""
    changed = []
    for total, line_type, symbol in lines:
        if total == 6:   # old yin becomes young yang
            changed.append((7, "young yang", "-----"))
        elif total == 9: # old yang becomes young yin
            changed.append((8, "young yin", "-- --"))
        else:
            changed.append((total, line_type, symbol))
    return changed

def display_hexagram(lines, number, label=""):
    print(f"\n  {'─'*20}")
    if label:
        print(f"  {label}")
    print(f"  Hexagram {number}")
    print(f"  {'─'*20}")
    for i, (total, line_type, symbol) in reversed(list(enumerate(lines))):
        changing = " ← changing" if total in (6, 9) else ""
        print(f"  Line {i+1}:  {symbol}  ({total}, {line_type}){changing}")
    print(f"  {'─'*20}")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading conversation history...")
    bits = load_bits("all_digits.txt")
    print(f"Ready. {len(bits):,} bits loaded.\n")

    while True:
        input("Press Enter to cast the hexagram...")

        lines = cast_hexagram()
        primary_num = lines_to_number(lines)
        has_changes = any(total in (6, 9) for total, _, _ in lines)

        display_hexagram(lines, primary_num, label="Primary Hexagram")

        if has_changes:
            changed_lines = changing_lines_to_number(lines)
            secondary_num = lines_to_number(changed_lines)
            display_hexagram(changed_lines, secondary_num, label="Relating Hexagram (after changes)")
            print(f"\n  Moving from Hexagram {primary_num} → {secondary_num}\n")
        else:
            print(f"\n  No changing lines. Hexagram {primary_num} is stable.\n")
