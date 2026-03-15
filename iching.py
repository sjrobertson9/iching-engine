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
    """Convert 6 lines to hexagram number (1-64)."""
    # Binary: yang=1, yin=0, bottom line = LSB
    binary = []
    for total, _, _ in lines:
        binary.append(1 if total in (7, 9) else 0)  # yang lines = 1
    # Convert to King Wen sequence via trigram lookup
    # Lower trigram = lines 1-3, upper = lines 4-6
    lower = binary[0] * 4 + binary[1] * 2 + binary[2]
    upper = binary[3] * 4 + binary[4] * 2 + binary[5]

    # King Wen sequence lookup table
    king_wen = [
        [1,  34, 5,  26, 11, 9,  14, 43],
        [25, 51, 3,  27, 24, 42, 21, 17],
        [6,  40, 29, 4,  7,  59, 64, 47],
        [33, 62, 39, 52, 15, 53, 56, 31],
        [12, 16, 8,  23, 2,  20, 35, 45],
        [44, 32, 48, 18, 46, 57, 50, 28],
        [13, 55, 63, 22, 36, 37, 30, 49],
        [10, 54, 60, 41, 19, 61, 38, 58],
    ]
    return king_wen[upper][lower]

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
