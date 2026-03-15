"""
Hexagram Pipeline v2 — SHA-256 Whitened
Replaces raw digit parity with SHA-256 hashed chunks for better entropy
then compares results to the original Von Neumann pipeline
"""

import numpy as np
import hashlib
from collections import defaultdict
import matplotlib.pyplot as plt

# ── ORIGINAL PIPELINE (for comparison) ───────────────────────────────────────

def load_digits(path="all_digits.txt"):
    with open(path, "r") as f:
        raw = f.read()
    return [int(c) for c in raw if c.isdigit()]

def von_neumann(digits):
    bits = []
    evens = [d % 2 for d in digits]
    i = 0
    while i + 1 < len(evens):
        a, b = evens[i], evens[i+1]
        if a != b:
            bits.append(a)
        i += 2
    return bits

# ── NEW PIPELINE: SHA-256 WHITENING ───────────────────────────────────────────

def sha256_whiten(digits, chunk_size=64):
    """
    Split digits into chunks, hash each chunk with SHA-256,
    extract bits from the hash output.
    This removes structural bias while preserving uniqueness.
    """
    digit_str = "".join(str(d) for d in digits)
    bits = []

    for i in range(0, len(digit_str) - chunk_size, chunk_size):
        chunk = digit_str[i:i+chunk_size].encode()
        hash_bytes = hashlib.sha256(chunk).digest()  # 32 bytes = 256 bits
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
    actual = len(hexagrams)
    if actual < n:
        print(f"Warning: only {actual:,} hexagrams generated")
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

# ── BIT QUALITY CHECK ─────────────────────────────────────────────────────────

def bit_quality_report(bits_vn, bits_sha, label_vn="Von Neumann", label_sha="SHA-256"):
    """Compare the two bit streams for bias and quality."""
    print(f"\n── Bit Stream Quality Report ──")

    for bits, label in [(bits_vn, label_vn), (bits_sha, label_sha)]:
        ones = sum(bits)
        zeros = len(bits) - ones
        balance = ones / len(bits)
        print(f"\n{label}:")
        print(f"  Total bits:  {len(bits):,}")
        print(f"  Ones:        {ones:,} ({balance*100:.2f}%)")
        print(f"  Zeros:       {zeros:,} ({(1-balance)*100:.2f}%)")
        print(f"  Bias from 50/50: {abs(balance - 0.5)*100:.3f}%")

        # Check for runs (long streaks of same bit)
        max_run = 1
        curr_run = 1
        for i in range(1, min(len(bits), 100000)):
            if bits[i] == bits[i-1]:
                curr_run += 1
                max_run = max(max_run, curr_run)
            else:
                curr_run = 1
        print(f"  Longest run (first 100k): {max_run} bits")

# ── ATTRACTOR REPORT ──────────────────────────────────────────────────────────

def attractor_report(hexagrams, label="", top_n=12):
    counts = np.bincount(hexagrams, minlength=65)[1:]
    ranked = np.argsort(counts)[::-1]
    total = len(hexagrams)
    print(f"\n── Top {top_n} Attractors ({label}) ──")
    for i in range(top_n):
        h = ranked[i] + 1
        print(f"  Hexagram {h:2d}: {counts[ranked[i]]} visits ({counts[ranked[i]]/total*100:.2f}%)")
    return counts

def markov_report(hexagrams, label="", top_n=10):
    counts = defaultdict(lambda: defaultdict(int))
    for a, b in zip(hexagrams, hexagrams[1:]):
        counts[a][b] += 1
    pairs = [(c, a, b) for a, t in counts.items() for b, c in t.items()]
    pairs.sort(reverse=True)
    print(f"\n── Top {top_n} Transitions ({label}) ──")
    for count, a, b in pairs[:top_n]:
        loop = " ↺" if a == b else ""
        print(f"  Hex {a:2d} → Hex {b:2d}  ({count}x){loop}")

# ── COMPARISON PLOT ───────────────────────────────────────────────────────────

def plot_comparison(hex_vn, hex_sha):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Von Neumann vs SHA-256 Whitened — Hexagram Analysis", fontsize=14)

    counts_vn = np.bincount(hex_vn, minlength=65)[1:]
    counts_sha = np.bincount(hex_sha, minlength=65)[1:]
    expected = len(hex_vn) / 64

    # Frequency distributions
    ax = axes[0, 0]
    ax.bar(range(1, 65), counts_vn, color='steelblue', edgecolor='white', linewidth=0.3)
    ax.axhline(expected, color='red', linestyle='--', alpha=0.7, label=f'Expected ({expected:.0f})')
    ax.set_title("Von Neumann Pipeline")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")
    ax.legend()

    ax = axes[0, 1]
    ax.bar(range(1, 65), counts_sha, color='mediumseagreen', edgecolor='white', linewidth=0.3)
    ax.axhline(expected, color='red', linestyle='--', alpha=0.7, label=f'Expected ({expected:.0f})')
    ax.set_title("SHA-256 Whitened Pipeline")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")
    ax.legend()

    # Deviation from uniform
    ax = axes[1, 0]
    diff_vn = counts_vn - expected
    colors = ['tomato' if d > 0 else 'steelblue' for d in diff_vn]
    ax.bar(range(1, 65), diff_vn, color=colors, edgecolor='white', linewidth=0.3)
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.set_title("Von Neumann — Deviation from Uniform")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count above/below expected")

    ax = axes[1, 1]
    diff_sha = counts_sha - expected
    colors = ['tomato' if d > 0 else 'steelblue' for d in diff_sha]
    ax.bar(range(1, 65), diff_sha, color=colors, edgecolor='white', linewidth=0.3)
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.set_title("SHA-256 — Deviation from Uniform")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count above/below expected")

    plt.tight_layout()
    plt.savefig("hexagram_whitened.png", dpi=150)
    print("\nPlot saved to hexagram_whitened.png")

    # Summary stats
    print(f"\n── Uniformity Summary ──")
    print(f"{'':20} {'Von Neumann':>15} {'SHA-256':>15}")
    print(f"{'Max deviation':20} {max(abs(diff_vn)):>15.1f} {max(abs(diff_sha)):>15.1f}")
    print(f"{'Std deviation':20} {np.std(diff_vn):>15.2f} {np.std(diff_sha):>15.2f}")
    print(f"{'Top attractor %':20} {counts_vn.max()/len(hex_vn)*100:>14.2f}% {counts_sha.max()/len(hex_sha)*100:>14.2f}%")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("Loading digits...")
    digits = load_digits("all_digits.txt")

    print("\nPipeline 1: Von Neumann")
    bits_vn = von_neumann(digits)
    hex_vn = bits_to_hexagrams(bits_vn, n=10000)

    print("\nPipeline 2: SHA-256 Whitening")
    bits_sha = sha256_whiten(digits)
    hex_sha = bits_to_hexagrams(bits_sha, n=10000)

    bit_quality_report(bits_vn, bits_sha)

    attractor_report(hex_vn, label="Von Neumann")
    attractor_report(hex_sha, label="SHA-256 Whitened")

    markov_report(hex_vn, label="Von Neumann")
    markov_report(hex_sha, label="SHA-256 Whitened")

    ent_vn = windowed_entropy(hex_vn)
    ent_sha = windowed_entropy(hex_sha)
    print(f"\n── Entropy Summary ──")
    print(f"Von Neumann — mean: {np.mean(ent_vn):.3f}, min: {np.min(ent_vn):.3f}, max: {np.max(ent_vn):.3f}")
    print(f"SHA-256     — mean: {np.mean(ent_sha):.3f}, min: {np.min(ent_sha):.3f}, max: {np.max(ent_sha):.3f}")

    plot_comparison(hex_vn, hex_sha)
    print("\nDone.")
