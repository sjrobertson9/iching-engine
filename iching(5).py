"""
I Ching Casting Engine
Three-coin method using SHA-256 whitened Claude conversation history
Logs all casts to a CSV named after the first question of the session.

Mode 1: Traditional  random cast, question held in mind
Mode 2: Anchored     question seeds your position in the bit stream
"""

import hashlib
import csv
import re
from datetime import datetime

# ── CSV LOGGING ───────────────────────────────────────────────────────────────

csv_writer = None
csv_file_handle = None

def init_csv(first_question, mode_label):
    global csv_writer, csv_file_handle
    safe = re.sub(r'[^\w\s-]', '', first_question or "neutral_cast")
    safe = re.sub(r'\s+', '_', safe.strip())[:50]
    filename = f"{safe}.csv"
    csv_file_handle = open(filename, 'w', newline='', encoding='utf-8')
    csv_writer = csv.writer(csv_file_handle)
    csv_writer.writerow(['timestamp', 'mode', 'question', 'primary_hex', 'relating_hex', 'changing_lines', 'line_values', 'bit_position'])
    csv_file_handle.flush()
    print(f"  Logging to: {filename}\n")

def log_cast(mode_label, question, primary_num, secondary_num, lines, bit_start=None):
    if csv_writer is None:
        return
    changing = [str(i+1) for i, (total,_,_) in enumerate(lines) if total in (6, 9)]
    line_vals = "-".join(str(total) for total,_,_ in lines)
    csv_writer.writerow([
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        mode_label,
        question or "(neutral)",
        primary_num,
        secondary_num or "",
        ",".join(changing) if changing else "",
        line_vals,
        bit_start if bit_start is not None else "",
    ])
    csv_file_handle.flush()

# ── BIT PIPELINE ──────────────────────────────────────────────────────────────

bits = []
bit_index = 0

def load_bits(path="all_digits.txt"):
    with open(path, "r") as f:
        raw = f.read()
    digit_str = "".join(c for c in raw if c.isdigit())
    result = []
    chunk_size = 64
    for i in range(0, len(digit_str) - chunk_size, chunk_size):
        chunk = digit_str[i:i+chunk_size].encode()
        hash_bytes = hashlib.sha256(chunk).digest()
        for byte in hash_bytes:
            for bit_pos in range(8):
                result.append((byte >> (7 - bit_pos)) & 1)
    return result

def set_position(pos):
    global bit_index
    bit_index = pos % len(bits)

def flip_coin():
    global bit_index
    if bit_index >= len(bits):
        bit_index = 0
    result = bits[bit_index]
    bit_index += 1
    return 3 if result == 1 else 2

# ── CASTING ───────────────────────────────────────────────────────────────────

def cast_line():
    total = flip_coin() + flip_coin() + flip_coin()
    if total == 6:   return total, "old yin",    "-- x --"
    elif total == 7: return total, "young yang", "-----"
    elif total == 8: return total, "young yin",  "-- --"
    elif total == 9: return total, "old yang",   "--o--"

def cast_hexagram():
    return [cast_line() for _ in range(6)]

def trigram_name(l1, l2, l3):
    y = tuple(1 if x in (7, 9) else 0 for x in (l1, l2, l3))
    names = {
        (1,1,1):'Qian', (0,0,0):'Kun',  (1,0,0):'Zhen', (1,1,0):'Dui',
        (0,1,0):'Kan',  (1,0,1):'Li',   (0,0,1):'Gen',  (0,1,1):'Xun',
    }
    return names[y]

def lines_to_number(lines):
    t = [total for total, _, _ in lines]
    upper = trigram_name(t[3], t[4], t[5])
    lower = trigram_name(t[0], t[1], t[2])
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
    changed = []
    for total, line_type, symbol in lines:
        if total == 6:   changed.append((7, "young yang", "-----"))
        elif total == 9: changed.append((8, "young yin",  "-- --"))
        else:            changed.append((total, line_type, symbol))
    return changed

# ── DISPLAY ───────────────────────────────────────────────────────────────────

def display_hexagram(lines, number, label=""):
    print(f"\n  {'─'*22}")
    if label: print(f"  {label}")
    print(f"  Hexagram {number}")
    print(f"  {'─'*22}")
    for i, (total, line_type, symbol) in reversed(list(enumerate(lines))):
        changing = "  <- changing" if total in (6, 9) else ""
        print(f"  Line {i+1}:  {symbol:<10} ({total}, {line_type}){changing}")
    print(f"  {'─'*22}")

def do_cast(question=None, mode_label=""):
    bit_start = bit_index
    lines = cast_hexagram()
    primary_num = lines_to_number(lines)
    has_changes = any(total in (6, 9) for total, _, _ in lines)
    if question:
        print(f'\n  ? "{question}"')
    display_hexagram(lines, primary_num, label="Primary Hexagram")
    if has_changes:
        changed_lines = changing_lines_to_number(lines)
        secondary_num = lines_to_number(changed_lines)
        display_hexagram(changed_lines, secondary_num, label="Relating Hexagram (after changes)")
        print(f"\n  --> Hexagram {primary_num} -> {secondary_num}\n")
        log_cast(mode_label, question, primary_num, secondary_num, lines, bit_start)
    else:
        print(f"\n  Hexagram {primary_num} is stable. No changing lines.\n")
        log_cast(mode_label, question, primary_num, None, lines, bit_start)

def question_to_offset(question):
    h = hashlib.sha256(question.strip().lower().encode()).digest()
    return int.from_bytes(h[:4], 'big') % len(bits)

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\nLoading conversation history...")
    bits = load_bits("all_digits.txt")
    print(f"Ready. {len(bits):,} bits loaded.\n")

    print("  +------------------------------------------+")
    print("  |          I CHING CASTING ENGINE          |")
    print("  +------------------------------------------+\n")
    print("  1  Traditional  random cast, question held in mind")
    print("  2  Anchored     question seeds your position in the bit stream\n")

    mode = ""
    while mode not in ("1", "2"):
        mode = input("  Choose mode (1 or 2): ").strip()
    mode_label = "traditional" if mode == "1" else "anchored"
    print()

    csv_initialized = False

    if mode == "1":
        # Seed starting position from current timestamp for fresh randomness each session
        import time
        bit_index = int(time.time() * 1000) % len(bits)
        set_position(bit_index)
        print(f"  Traditional mode. Session seeded at bit {bit_index:,}.")
        print("  Type EXIT to quit.\n")
        while True:
            question = input("  Your question (or Enter for neutral cast): ").strip()
            if question.upper() == "EXIT":
                print("\n  The oracle rests.\n"); break
            if not csv_initialized:
                init_csv(question if question else "neutral_cast", mode_label)
                csv_initialized = True
            input("  Press Enter to cast...")
            do_cast(question if question else None, mode_label)

    elif mode == "2":
        print("  Anchored mode. Your question seeds the bit stream.")
        print("  Same question = same starting position. Each cast advances from there.")
        print("  Type EXIT to quit.\n")
        current_question = None
        while True:
            question = input("  Your question (Enter to reuse last, EXIT to quit): ").strip()
            if question.upper() == "EXIT":
                print("\n  The oracle rests.\n"); break
            if question:
                current_question = question
                if not csv_initialized:
                    init_csv(current_question, mode_label)
                    csv_initialized = True
                pos = question_to_offset(current_question)
                set_position(pos)
                print(f"  Anchored to bit {pos:,} of {len(bits):,}")
            elif current_question is None:
                print("  (enter a question first)\n"); continue
            else:
                print(f"  Continuing from bit {bit_index:,} for: \"{current_question}\"")
            input("  Press Enter to cast...")
            do_cast(current_question, mode_label)

    if csv_file_handle:
        csv_file_handle.close()
