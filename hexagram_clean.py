"""
Hexagram Analysis — Dip Zone Removed
Excludes positions 7200-7400 (the zeros dip) and reruns attractor + Markov stats
"""

import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

# ── PIPELINE ──────────────────────────────────────────────────────────────────

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

# ── MARKOV ────────────────────────────────────────────────────────────────────

def markov_report(hexagrams, label="", top_n=12):
    counts = defaultdict(lambda: defaultdict(int))
    for a, b in zip(hexagrams, hexagrams[1:]):
        counts[a][b] += 1

    pairs = []
    for a, trans in counts.items():
        for b, c in trans.items():
            pairs.append((c, a, b))
    pairs.sort(reverse=True)

    print(f"\n── Top {top_n} Transitions ({label}) ──")
    for count, a, b in pairs[:top_n]:
        loop = " ↺" if a == b else ""
        print(f"  Hex {a:2d} → Hex {b:2d}  ({count}x){loop}")

    return counts

def attractor_report(hexagrams, label="", top_n=12):
    counts = np.bincount(hexagrams, minlength=65)[1:]
    ranked = np.argsort(counts)[::-1]
    total = len(hexagrams)

    print(f"\n── Top {top_n} Attractors ({label}) ──")
    for i in range(top_n):
        h = ranked[i] + 1
        print(f"  Hexagram {h:2d}: {counts[ranked[i]]} visits ({counts[ranked[i]]/total*100:.2f}%)")
    return counts

# ── PLOT ──────────────────────────────────────────────────────────────────────

def plot_comparison(full_hex, clean_hex, entropies_full, entropies_clean):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Hexagram Analysis — Full vs Dip-Removed", fontsize=14)

    # Full frequency distribution
    ax = axes[0, 0]
    ax.bar(range(1, 65), np.bincount(full_hex, minlength=65)[1:],
           color='steelblue', edgecolor='white', linewidth=0.3)
    ax.set_title("Full Sequence (with dip)")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")
    ax.axvline(64, color='red', linestyle='--', alpha=0.5, label='Hex 64')
    ax.axvline(1, color='orange', linestyle='--', alpha=0.5, label='Hex 1')
    ax.legend(fontsize=8)

    # Clean frequency distribution
    ax = axes[0, 1]
    counts_clean = np.bincount(clean_hex, minlength=65)[1:]
    colors = ['tomato' if c == counts_clean.max() else 'mediumseagreen' for c in counts_clean]
    ax.bar(range(1, 65), counts_clean, color=colors, edgecolor='white', linewidth=0.3)
    ax.set_title("Dip-Removed Sequence")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")

    # Entropy comparison
    ax = axes[1, 0]
    ax.plot(entropies_full, color='steelblue', alpha=0.7, label='Full')
    ax.plot(entropies_clean, color='mediumseagreen', alpha=0.9, label='Dip removed')
    ax.axhline(np.mean(entropies_full), color='steelblue', linestyle='--', alpha=0.4)
    ax.axhline(np.mean(entropies_clean), color='mediumseagreen', linestyle='--', alpha=0.4)
    ax.set_title("Entropy Over Time")
    ax.set_xlabel("Window")
    ax.set_ylabel("Entropy (bits)")
    ax.legend()

    # Difference plot (clean counts - expected uniform)
    ax = axes[1, 1]
    expected = len(clean_hex) / 64
    diff = counts_clean - expected
    colors = ['tomato' if d > 0 else 'steelblue' for d in diff]
    ax.bar(range(1, 65), diff, color=colors, edgecolor='white', linewidth=0.3)
    ax.axhline(0, color='gray', linewidth=0.8)
    ax.set_title("Deviation from Uniform (clean sequence)\nRed = over-represented, Blue = under")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count above/below expected")

    plt.tight_layout()
    plt.savefig("hexagram_clean.png", dpi=150)
    print("\nPlot saved to hexagram_clean.png")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    digits = load_digits("all_digits.txt")
    bits = von_neumann(digits)
    full_hex = bits_to_hexagrams(bits, n=10000)

    # Remove dip zone (positions 7200–7400)
    DIP_START, DIP_END = 7200, 7400
    clean_hex = full_hex[:DIP_START] + full_hex[DIP_END:]
    print(f"Full sequence: {len(full_hex):,} hexagrams")
    print(f"Clean sequence: {len(clean_hex):,} hexagrams (removed positions {DIP_START}–{DIP_END})")

    attractor_report(full_hex, label="full")
    attractor_report(clean_hex, label="dip removed")

    markov_report(full_hex, label="full")
    markov_report(clean_hex, label="dip removed")

    entropies_full = windowed_entropy(full_hex)
    entropies_clean = windowed_entropy(clean_hex)
    print(f"\nFull entropy    — mean: {np.mean(entropies_full):.3f}, min: {np.min(entropies_full):.3f}")
    print(f"Clean entropy   — mean: {np.mean(entropies_clean):.3f}, min: {np.min(entropies_clean):.3f}")

    plot_comparison(full_hex, clean_hex, entropies_full, entropies_clean)
    print("\nDone.")
