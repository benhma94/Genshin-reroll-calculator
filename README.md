# Genshin Reshaping Odds Calculator

A random tool I made for fun for Genshin Impact.

## What it does

Calculates the odds of improvement when reshaping an artifact. As the guarantee is dependent on the order of rolls, this calculator takes that into account. At a base level this calculator determines whether RV will increase.
Results will display
- **P(improve):** chance the reshaped result beats your current artifact
- **P(equal):** chance it matches
- **P(worse):** chance it comes out worse

## Features

- **Combined mode** — compares the RV of all stats against your current RV
- **Single-stat mode** — focuses on the probability for one specific stat or group
- **Stat grouping** — CR/CD are treated as a group (C), FH/FA/FD as a group (F)
- **Guarantee mechanics** — model guaranteed minimum rolls on a stat group (e.g. at least 2 rolls landing on C)
- **Custom weights** — assign different multipliers to each stat in combined mode. Apply a weight of 2 to CR, and 1 to CD to calculate Crit Value.
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
