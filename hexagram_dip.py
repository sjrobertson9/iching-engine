"""
Hexagram Dip Zone Investigation
- Finds the entropy dip
- Shows what hexagrams cluster there
- Compares dip zone vs full sequence
- Saves a focused plot
"""

import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt

# ── PIPELINE (same as before) ─────────────────────────────────────────────────

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

# ── DIP INVESTIGATION ─────────────────────────────────────────────────────────

def investigate_dip(hexagrams, digits, window=200):
    entropies = windowed_entropy(hexagrams, window)
    dip_idx = int(np.argmin(entropies))
    dip_start = dip_idx * window
    dip_end = dip_start + window
    dip_hexes = hexagrams[dip_start:dip_end]

    print(f"\n── Where is the dip? ──")
    print(f"Window {dip_idx} out of {len(entropies)} total windows")
    print(f"Hexagram positions {dip_start} to {dip_end} in the 10,000-step sequence")
    print(f"Entropy here: {entropies[dip_idx]:.3f} bits  (mean is {np.mean(entropies):.3f})")

    # Approximate location in raw digit file
    approx_start = dip_start * 6 * 2
    approx_end = dip_end * 6 * 2
    pct_start = approx_start / len(digits) * 100
    pct_end = approx_end / len(digits) * 100
    print(f"Approx location in all_digits.txt: {approx_start:,}–{approx_end:,} chars ({pct_start:.1f}%–{pct_end:.1f}% through)")

    # What hexagrams dominate the dip?
    dip_counts = np.bincount(dip_hexes, minlength=65)[1:]
    all_counts = np.bincount(hexagrams, minlength=65)[1:]
    ranked = np.argsort(dip_counts)[::-1]

    print(f"\n── What's in the dip? ──")
    print(f"{'Hexagram':<12} {'Dip %':<10} {'Overall %':<12} {'Ratio':<8}")
    print("-" * 44)
    for i in range(15):
        h = ranked[i] + 1
        d_pct = dip_counts[ranked[i]] / window * 100
        a_pct = all_counts[ranked[i]] / len(hexagrams) * 100
        ratio = d_pct / a_pct if a_pct > 0 else 0
        if d_pct > 0:
            marker = " ◄ DOMINANT" if ratio > 3 else ""
            print(f"Hex {h:<8} {d_pct:<10.1f} {a_pct:<12.1f} ×{ratio:<7.1f}{marker}")

    # Self-loops in dip vs overall
    dip_loops = sum(1 for a, b in zip(dip_hexes, dip_hexes[1:]) if a == b)
    all_loops = sum(1 for a, b in zip(hexagrams, hexagrams[1:]) if a == b)
    print(f"\n── Self-loops (same hexagram repeating back to back) ──")
    print(f"Dip zone:       {dip_loops}/{window-1} = {dip_loops/(window-1)*100:.1f}%")
    print(f"Full sequence:  {all_loops}/{len(hexagrams)-1} = {all_loops/(len(hexagrams)-1)*100:.1f}%")

    return entropies, dip_idx, dip_hexes, dip_counts, all_counts

# ── PLOT ──────────────────────────────────────────────────────────────────────

def plot_dip(hexagrams, entropies, dip_idx, dip_hexes, dip_counts, all_counts, window=200):
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle("Entropy Dip Zone — Deep Dive", fontsize=14)

    # 1. Entropy with dip marked
    ax = axes[0, 0]
    ax.plot(entropies, color='darkorange', linewidth=1.5)
    ax.axvline(dip_idx, color='red', linestyle='--', linewidth=2)
    ax.fill_between(range(len(entropies)),
                    [entropies[dip_idx]]*len(entropies),
                    entropies,
                    where=[i == dip_idx for i in range(len(entropies))],
                    alpha=0.3, color='red')
    ax.axhline(np.mean(entropies), color='gray', linestyle='--', alpha=0.7, label='Mean')
    ax.set_title("Entropy — Dip Marked in Red")
    ax.set_xlabel("Window")
    ax.set_ylabel("Entropy (bits)")
    ax.legend()

    # 2. Dip zone hexagram counts
    ax = axes[0, 1]
    colors = ['red' if dip_counts[i]/window > 0.05 else 'steelblue' for i in range(64)]
    ax.bar(range(1, 65), dip_counts, color=colors, edgecolor='white', linewidth=0.3)
    ax.set_title("Hexagram Counts in Dip Zone\n(red = >5% of window)")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Count")

    # 3. Dip vs overall comparison (top 20 hexagrams by dip count)
    ax = axes[1, 0]
    top20 = np.argsort(dip_counts)[::-1][:20]
    x = np.arange(20)
    ax.bar(x - 0.2, dip_counts[top20] / window * 100, width=0.4, label='Dip zone', color='red', alpha=0.7)
    ax.bar(x + 0.2, all_counts[top20] / len(hexagrams) * 100, width=0.4, label='Full sequence', color='steelblue', alpha=0.7)
    ax.set_xticks(x)
    ax.set_xticklabels([str(i+1) for i in top20], fontsize=8)
    ax.set_title("Dip Zone vs Full Sequence (top 20 by dip count)")
    ax.set_xlabel("Hexagram")
    ax.set_ylabel("Frequency %")
    ax.legend()

    # 4. Sequence of hexagrams in dip zone (show the actual flow)
    ax = axes[1, 1]
    ax.plot(range(len(dip_hexes)), dip_hexes, color='purple', linewidth=0.8, alpha=0.7)
    ax.set_title(f"Hexagram Sequence Inside Dip (positions {dip_idx*window}–{(dip_idx+1)*window})")
    ax.set_xlabel("Step")
    ax.set_ylabel("Hexagram")
    ax.set_ylim(0, 65)

    plt.tight_layout()
    plt.savefig("hexagram_dip.png", dpi=150)
    print("\nPlot saved to hexagram_dip.png")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    digits = load_digits("all_digits.txt")
    bits = von_neumann(digits)
    hexagrams = bits_to_hexagrams(bits, n=10000)

    entropies, dip_idx, dip_hexes, dip_counts, all_counts = investigate_dip(hexagrams, digits)
    plot_dip(hexagrams, entropies, dip_idx, dip_hexes, dip_counts, all_counts)

    print("\nDone.")
