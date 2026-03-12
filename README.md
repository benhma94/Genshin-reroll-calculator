# Genshin Reshaping Odds Calculator

A desktop GUI tool for analyzing the probability of improving artifact sub-stats through Genshin Impact's reshaping mechanic.

## What it does

When reshaping an artifact, 4 stats are randomly selected from your chosen pool and each receives a multiplier of 70%, 80%, 90%, or 100%. This tool computes the full probability distribution over all possible outcomes and tells you:

- **P(improve):** chance the reshaped result beats your current artifact
- **P(equal):** chance it matches
- **P(worse):** chance it comes out worse

## Features

- **Combined mode** — compares the weighted sum of all stats against your current total
- **Single-stat mode** — focuses on the probability for one specific stat or group
- **Stat grouping** — CR/CD are treated as a group (C), FH/FA/FD as a group (F)
- **Guarantee mechanics** — model guaranteed minimum rolls on a stat group (e.g. at least 2 rolls landing on C)
- **Custom weights** — assign different multipliers to each stat in combined mode
- **Good/bad stat filtering** — exclude off-stats from contributing to the combined score

## Requirements

- Python 3 (standard library only — no additional installs needed)
- `tkinter` (included with most Python distributions)

## How to run

```bash
python reshaping_odds.py
```

## Usage

1. **Select stats** — check the stats present on your artifact
2. **Set roll count** — choose 4 or 5 rolls
3. **Set guarantee** — if applicable, set the guaranteed count for a stat group
4. **Enter base values** — input your current stat values (as percentages, e.g. 152 for 152%)
5. **Choose mode** — combined or single-stat
6. **Click Analyze** — results appear in the output panel
