"""
Hexagram Pipeline v3 — SHA-256 Whitened + Dead Zone Removal
Removes all known low-variation zones before hashing, then compares to v2
"""

import numpy as np
import hashlib
from collections import defaultdict
import matplotlib.pyplot as plt

# ── KNOWN DEAD ZONES (from Gemini characterization report) ───────────────────
# Format: (start, end) character positions in all_digits.txt

DEAD_ZONES = [
    (31700, 32300),
    (32500, 35000),
    (44100, 44700),
    (48300, 48900),
    (54400, 55500),
    (60700, 61200),
    (86400, 88800),   # the zeros dip we found first
    (169400, 170500),
    (183000, 186400),  # worst zone — 500250025002...
    (222400, 223000),
    (378000, 378900),
    (379000, 379700),
    (501600, 502400),
    (503400, 504200),
]

# ── PIPELINE ──────────────────────────────────────────────────────────────────

def load_raw(path="all_digits.txt"):
    with open(path, "r") as f:
        return f.read()

def extract_digits(raw):
    return [int(c) for c in raw if c.isdigit()]

def remove_dead_zones(digit_str):
    """Remove known dead zone character ranges from the digit string."""
    # Work on the raw string, masking out dead zones
    chars = list(digit_str)
    total_removed = 0
    for start, end in sorted(DEAD_ZONES, reverse=True):
        removed = end - start
        chars[start:end] = []
        total_removed += removed
    cleaned = "".join(chars)
    print(f"Dead zone removal: {len(digit_str):,} → {len(cleaned):,} chars ({total_removed:,} removed across {len(DEAD_ZONES)} zones)")
    return cleaned

def sha256_whiten(digit_str, chunk_size=64):
    bits = []
    for i in range(0, len(digit_str) - chunk_size, chunk_size):
        chunk = digit_str[i:i+chunk_size].encode()
        hash_bytes = hashlib.sha256(chunk).digest()
        for byte in hash_bytes:
            for bit_pos in range(8):
                bits.append((byte >> (7 - bit_pos)) & 1)
    print(f"SHA-256 whitening: {len(digit_str)//chunk_size:,} chunks → {len(bits):,} bits")
    return bits

def bits_to_hexagrams(bits, n=10000):
    hexagrams = []
    i = 0
    while len(hexagrams) < n and i + 6 <= len(bits):
        chunk = bits[i:i+6]
        hexagrams.append(int("".join(str(b) for b in chunk), 2) + 1)
        i += 6
    return hexagrams[:n]

def windowed_entropy(hexagrams, window=200):
    entropies = []
    for i in range(0, len(hexagrams) - window, window):
        w = hexagrams[i:i+window]
        counts = np.bincount(w, minlength=65)[1:]
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        entropies.append(-np.sum(probs * np.log2(probs)))
    return entropies

def attractor_report(hexagrams, label="", top_n=12):
    counts = np.bincount(hexagrams, minlength=65)[1:]
    ranked = np.argsort(counts)[::-1]
    total = len(hexagrams)
    print(f"\n── Top {top_n} Attractors ({label}) ──")
    for i in range(top_n):
        h = ranked[i] + 1
        print(f"  Hexagram {h:2d}: {counts[ranked[i]]} visits ({counts[ranked[i]]/total*100:.2f}%)")
    return counts

def markov_report(hexagrams, label="", top_n=8):
    counts = defaultdict(lambda: defaultdict(int))
    for a, b in zip(hexagrams, hexagrams[1:]):
        counts[a][b] += 1
    pairs = [(c, a, b) for a, t in counts.items() for b, c in t.items()]
    pairs.sort(reverse=True)
    print(f"\n── Top {top_n} Transitions ({label}) ──")
    for count, a, b in pairs[:top_n]:
        loop = " ↺" if a == b else ""
        print(f"  Hex {a:2d} → Hex {b:2d}  ({count}x){loop}")

# ── PLOT ──────────────────────────────────────────────────────────────────────

def plot_comparison(hex_sha, hex_clean, ent_sha, ent_clean):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("SHA-256 vs SHA-256 + Dead Zone Removal", fontsize=14)

    expected = 10000 / 64
    counts_sha = np.bincount(hex_sha, minlength=65)[1:]
    counts_clean = np.bincount(hex_clean, minlength=65)[1:]

    # Frequency distributions
    ax = axes[0, 0]
    ax.bar(range(1, 65), counts_sha, color='mediumseagreen', edgecolor='white', linewidth=0.3)
    ax.axhline(expected, color='red', linestyle='--', alpha=0.7, label=f'Expected ({expected:.0f})')
    ax.set_title("SHA-256 Only")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")
    ax.legend()

    ax = axes[0, 1]
    ax.bar(range(1, 65), counts_clean, color='mediumpurple', edgecolor='white', linewidth=0.3)
    ax.axhline(expected, color='red', linestyle='--', alpha=0.7, label=f'Expected ({expected:.0f})')
    ax.set_title("SHA-256 + Dead Zones Removed")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")
    ax.legend()

    # Entropy over time
    ax = axes[1, 0]
    ax.plot(ent_sha, color='mediumseagreen', linewidth=1.5, label='SHA-256')
    ax.plot(ent_clean, color='mediumpurple', linewidth=1.5, label='+ Dead zones removed', alpha=0.8)
    ax.axhline(np.mean(ent_sha), color='mediumseagreen', linestyle='--', alpha=0.4)
    ax.axhline(np.mean(ent_clean), color='mediumpurple', linestyle='--', alpha=0.4)
    ax.set_title("Entropy Over Time")
    ax.set_xlabel("Window")
    ax.set_ylabel("Entropy (bits)")
    ax.legend()

    # Deviation comparison
    ax = axes[1, 1]
    diff_sha = counts_sha - expected
    diff_clean = counts_clean - expected
    x = np.arange(64)
    ax.bar(x - 0.2, diff_sha, width=0.4, color='mediumseagreen', alpha=0.7, label='SHA-256')
    ax.bar(x + 0.2, diff_clean, width=0.4, color='mediumpurple', alpha=0.7, label='+ Dead zones removed')
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.set_title("Deviation from Uniform — Side by Side")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count above/below expected")
    ax.legend()

    plt.tight_layout()
    plt.savefig("hexagram_v3.png", dpi=150)
    print("\nPlot saved to hexagram_v3.png")

    # Summary
    print(f"\n── Final Uniformity Summary ──")
    print(f"{'':25} {'SHA-256':>12} {'SHA-256 + Clean':>16}")
    print(f"{'Max deviation':25} {max(abs(diff_sha)):>12.1f} {max(abs(diff_clean)):>16.1f}")
    print(f"{'Std deviation':25} {np.std(diff_sha):>12.2f} {np.std(diff_clean):>16.2f}")
    print(f"{'Top attractor %':25} {counts_sha.max()/10000*100:>11.2f}% {counts_clean.max()/10000*100:>15.2f}%")
    print(f"{'Entropy mean':25} {np.mean(ent_sha):>12.3f} {np.mean(ent_clean):>16.3f}")
    print(f"{'Entropy min':25} {np.min(ent_sha):>12.3f} {np.min(ent_clean):>16.3f}")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    raw = load_raw("all_digits.txt")
    digit_str = "".join(c for c in raw if c.isdigit())

    print("\nPipeline 2: SHA-256 only")
    bits_sha = sha256_whiten(digit_str)
    hex_sha = bits_to_hexagrams(bits_sha, n=10000)

    print("\nPipeline 3: SHA-256 + Dead Zone Removal")
    cleaned_str = remove_dead_zones(digit_str)
    bits_clean = sha256_whiten(cleaned_str)
    hex_clean = bits_to_hexagrams(bits_clean, n=10000)

    attractor_report(hex_sha, label="SHA-256 only")
    attractor_report(hex_clean, label="SHA-256 + dead zones removed")

    markov_report(hex_sha, label="SHA-256 only")
    markov_report(hex_clean, label="SHA-256 + dead zones removed")

    ent_sha = windowed_entropy(hex_sha)
    ent_clean = windowed_entropy(hex_clean)

    plot_comparison(hex_sha, hex_clean, ent_sha, ent_clean)
    print("\nDone.")
