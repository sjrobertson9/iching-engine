"""
Hexagram Analysis Pipeline
Reads all_digits.txt, generates 10,000 hexagrams, and runs:
- Markov Chain transition matrix
- Shannon entropy windowed analysis
- Spectral density (FFT)
- Basic attractor/frequency report
"""

import numpy as np
from collections import defaultdict
import matplotlib.pyplot as plt
from scipy.fft import fft, fftfreq

# ── 1. LOAD & EXTRACT DIGITS ─────────────────────────────────────────────────

def load_digits(path="all_digits.txt"):
    with open(path, "r") as f:
        raw = f.read()
    # Keep only numeric characters
    digits = [int(c) for c in raw if c.isdigit()]
    print(f"Loaded {len(digits):,} digits from {path}")
    return digits

# ── 2. VON NEUMANN DECORRELATOR → FAIR BITS ──────────────────────────────────

def von_neumann(digits):
    """Converts raw digits to a debiased binary stream."""
    bits = []
    evens = [d % 2 for d in digits]  # parity of each digit
    i = 0
    while i + 1 < len(evens):
        a, b = evens[i], evens[i+1]
        if a != b:
            bits.append(a)
        i += 2
    print(f"Von Neumann produced {len(bits):,} fair bits")
    return bits

# ── 3. BITS → HEXAGRAMS (Mod 64) ─────────────────────────────────────────────

def bits_to_hexagrams(bits, n=10000):
    hexagrams = []
    i = 0
    while len(hexagrams) < n and i + 6 <= len(bits):
        chunk = bits[i:i+6]
        value = int("".join(str(b) for b in chunk), 2)  # 0–63
        hexagrams.append(value + 1)  # 1–64
        i += 6
    if len(hexagrams) < n:
        print(f"Warning: only generated {len(hexagrams):,} hexagrams (not enough bits)")
    else:
        print(f"Generated {len(hexagrams):,} hexagrams")
    return hexagrams[:n]

# ── 4. MARKOV CHAIN ───────────────────────────────────────────────────────────

def markov_matrix(hexagrams):
    counts = defaultdict(lambda: defaultdict(int))
    for a, b in zip(hexagrams, hexagrams[1:]):
        counts[a][b] += 1

    # Normalize to probabilities
    matrix = {}
    for state, transitions in counts.items():
        total = sum(transitions.values())
        matrix[state] = {k: v/total for k, v in transitions.items()}

    # Top 5 most likely transitions overall
    print("\n── Top 10 Most Frequent Transitions ──")
    pairs = []
    for a, trans in counts.items():
        for b, c in trans.items():
            pairs.append((c, a, b))
    pairs.sort(reverse=True)
    for count, a, b in pairs[:10]:
        print(f"  Hex {a:2d} → Hex {b:2d}  ({count} times)")

    return matrix

# ── 5. SHANNON ENTROPY (windowed) ────────────────────────────────────────────

def windowed_entropy(hexagrams, window=200):
    entropies = []
    for i in range(0, len(hexagrams) - window, window):
        window_data = hexagrams[i:i+window]
        counts = np.bincount(window_data, minlength=65)[1:]
        probs = counts / counts.sum()
        probs = probs[probs > 0]
        H = -np.sum(probs * np.log2(probs))
        entropies.append(H)
    return entropies

# ── 6. SPECTRAL DENSITY (FFT) ─────────────────────────────────────────────────

def spectral_analysis(hexagrams):
    signal = np.array(hexagrams, dtype=float) - 32.5  # center around 0
    spectrum = np.abs(fft(signal))
    freqs = fftfreq(len(signal))
    # Only positive frequencies
    pos = freqs > 0
    return freqs[pos], spectrum[pos]

# ── 7. ATTRACTOR REPORT ───────────────────────────────────────────────────────

def attractor_report(hexagrams, top_n=10):
    counts = np.bincount(hexagrams, minlength=65)[1:]
    ranked = np.argsort(counts)[::-1]
    print(f"\n── Top {top_n} Attractor Hexagrams ──")
    for i in range(top_n):
        h = ranked[i] + 1
        print(f"  Hexagram {h:2d}: {counts[ranked[i]]} visits ({counts[ranked[i]]/len(hexagrams)*100:.1f}%)")
    if 64 in [ranked[i]+1 for i in range(top_n)]:
        print("  *** Hexagram 64 (Before Completion) is a major attractor ***")

# ── 8. PLOT ───────────────────────────────────────────────────────────────────

def plot_all(hexagrams, entropies, freqs, spectrum):
    fig, axes = plt.subplots(3, 1, figsize=(14, 12))
    fig.suptitle("Hexagram Analysis — 10,000 Step Sequence", fontsize=14)

    # Frequency distribution
    axes[0].hist(hexagrams, bins=64, range=(1, 65), color="steelblue", edgecolor="white", linewidth=0.3)
    axes[0].set_title("Hexagram Frequency Distribution")
    axes[0].set_xlabel("Hexagram (1–64)")
    axes[0].set_ylabel("Count")
    axes[0].axvline(64, color="red", linestyle="--", label="Hex 64")
    axes[0].legend()

    # Windowed entropy
    axes[1].plot(entropies, color="darkorange")
    axes[1].set_title("Shannon Entropy Over Time (window=200)")
    axes[1].set_xlabel("Window Index")
    axes[1].set_ylabel("Entropy (bits)")
    axes[1].axhline(np.mean(entropies), color="gray", linestyle="--", label="Mean")
    axes[1].legend()

    # Spectral density
    axes[2].plot(freqs[:500], spectrum[:500], color="mediumseagreen", linewidth=0.8)
    axes[2].set_title("Spectral Density (FFT) — Low Frequencies")
    axes[2].set_xlabel("Frequency")
    axes[2].set_ylabel("Amplitude")

    plt.tight_layout()
    plt.savefig("hexagram_analysis.png", dpi=150)
    print("\nPlot saved to hexagram_analysis.png")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    digits = load_digits("all_digits.txt")
    bits = von_neumann(digits)
    hexagrams = bits_to_hexagrams(bits, n=10000)

    markov_matrix(hexagrams)
    attractor_report(hexagrams)

    entropies = windowed_entropy(hexagrams)
    freqs, spectrum = spectral_analysis(hexagrams)

    print(f"\nEntropy — mean: {np.mean(entropies):.3f} bits, min: {np.min(entropies):.3f}, max: {np.max(entropies):.3f}")

    plot_all(hexagrams, entropies, freqs, spectrum)
    print("\nDone.")
