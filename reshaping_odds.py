import itertools
from collections import defaultdict
import tkinter as tk
from tkinter import scrolledtext, messagebox

# --- Constants ---

ALL_STATS = ['HP%', 'ATK%', 'CR', 'CD', 'ER', 'EM', 'FH', 'FA', 'FD', 'Def%']

COLLAPSE = {'CR': 'C', 'CD': 'C', 'FH': 'F', 'FA': 'F', 'FD': 'F'}

GROUPS = [
    ("Other", ['HP%', 'ATK%', 'ER', 'EM', 'Def%']),
    ("C-group  (→ C)", ['CR', 'CD']),
    ("F-group  (→ F)", ['FH', 'FA', 'FD']),
]

MULTIPLIERS = [7, 8, 9, 10]  # 70%, 80%, 90%, 100% as integer tenths


def collapsed_name(s):
    return COLLAPSE.get(s, s)


# --- Analysis ---

def convolve_dists(dist_a, dist_b):
    result = defaultdict(float)
    for va, pa in dist_a.items():
        for vb, pb in dist_b.items():
            result[va + vb] += pa * pb
    return dict(result)


def prob_summary(dist, base_internal):
    """Given {internal_value: probability}, compare against base_internal.
    Returns (p_greater, p_equal, p_less) as percentages."""
    p_gt = sum(p for v, p in dist.items() if v > base_internal)
    p_eq = sum(p for v, p in dist.items() if v == base_internal)
    p_lt = sum(p for v, p in dist.items() if v < base_internal)
    return p_gt * 100, p_eq * 100, p_lt * 100


def run_analysis(selected_stats, num_rolls, guarantee_stats, guarantee_count, bases,
                 mode='combined', focus=None, weights=None):
    """
    mode: 'combined' → compare grand total vs sum of all bases
          'single'   → compare one stat/label vs its base
    focus: for 'single' mode — a raw stat (e.g. 'CR') or collapsed label (e.g. 'C')
    weights: dict of stat → float multiplier for combined mode scoring. Defaults to all 1.0.
             Ignored in single stat mode.
    """
    if weights is None:
        weights = {s: 1.0 for s in selected_stats}

    # Effective bases: weighted for combined mode, unweighted for single stat mode
    if mode == 'combined':
        eff_bases = {s: bases[s] * weights[s] for s in selected_stats}
    else:
        eff_bases = bases

    lines = []
    out = lines.append

    stat_outcomes = list(itertools.product(selected_stats, repeat=num_rolls))
    n = len(selected_stats)
    n_stat = len(stat_outcomes)
    p_per_stat_path = 1.0 / n_stat

    collapsed_labels = sorted(set(collapsed_name(s) for s in selected_stats))

    # Header
    rolls_str = 'x'.join([str(n)] * num_rolls)
    out(f"Selected: {', '.join(selected_stats)}   Rolls: {num_rolls}   Paths: {rolls_str} = {n_stat}")
    out(f"Base: {', '.join(f'{s}={bases[s]}' for s in selected_stats)}  →  Total: {sum(bases.values())}%")
    non_default_weights = {s: w for s, w in weights.items() if w != 1.0}
    if non_default_weights:
        out(f"Weights: {', '.join(f'{s}={w:.1f}' for s, w in weights.items())}")
    out("Each roll tier: 70% / 80% / 90% / 100%  (equal probability)")

    # Determine what distribution to extract and what base to compare against
    focus_is_raw = (mode == 'single' and focus in selected_stats)
    focus_needs_raw_dist = focus_is_raw and collapsed_name(focus) != focus  # e.g. CR, CD, FH…

    def fmt(v):
        return str(int(v)) if v == int(v) else f"{v:.1f}"

    if mode == 'combined':
        focus_base_display = sum(eff_bases[s] for s in selected_stats)
        focus_label = "All stats (weighted)" if non_default_weights else "All stats"
    elif focus_is_raw:
        focus_base_display = bases[focus]
        focus_label = focus
    else:  # collapsed label
        members = [s for s in selected_stats if collapsed_name(s) == focus]
        focus_base_display = sum(bases[s] for s in members)
        focus_label = f"{focus} ({' + '.join(members)})" if len(members) > 1 else focus

    focus_base_internal = focus_base_display * 10  # internal = display * 10

    out(f"\nFocus: {focus_label}  |  Current base: {fmt(focus_base_display)}%")

    # --- Marginal computation ---

    def compute_marginals(stat_path):
        """Returns (per_collapsed, per_raw) distribution dicts."""
        per_collapsed = {}
        for lbl in collapsed_labels:
            dist = {0: 1.0}
            for s in stat_path:
                if collapsed_name(s) == lbl:
                    new_dist = defaultdict(float)
                    for v, p in dist.items():
                        for m in MULTIPLIERS:
                            new_dist[v + eff_bases[s] * m] += p * 0.25
                    dist = dict(new_dist)
            per_collapsed[lbl] = dist

        per_raw = {}
        if focus_needs_raw_dist:
            dist = {0: 1.0}
            for s in stat_path:
                if s == focus:
                    new_dist = defaultdict(float)
                    for v, p in dist.items():
                        for m in MULTIPLIERS:
                            new_dist[v + eff_bases[s] * m] += p * 0.25
                    dist = dict(new_dist)
            per_raw[focus] = dist

        return per_collapsed, per_raw

    def extract_focus_dist(per_collapsed, per_raw):
        if mode == 'combined':
            grand = {0: 1.0}
            for lbl in collapsed_labels:
                grand = convolve_dists(grand, per_collapsed[lbl])
            return grand
        elif focus_needs_raw_dist:
            return per_raw[focus]
        elif focus_is_raw:
            return per_collapsed[collapsed_name(focus)]
        else:
            return per_collapsed[focus]

    def format_phase(label, rollup):
        p_gt, p_eq, p_lt = prob_summary(rollup, focus_base_internal)
        base_str = fmt(focus_base_display)
        out(f"\n=== {label} ===")
        out(f"  P(improve: {focus_label} > {base_str}%) = {p_gt:6.2f}%")
        out(f"  P(same:    {focus_label} = {base_str}%) = {p_eq:6.2f}%")
        out(f"  P(worse:   {focus_label} < {base_str}%) = {p_lt:6.2f}%")

    # --- Phase 2: no guarantee ---
    rollup2 = defaultdict(float)
    for stat_path in stat_outcomes:
        per_collapsed, per_raw = compute_marginals(stat_path)
        for v, p in extract_focus_dist(per_collapsed, per_raw).items():
            rollup2[v] += p_per_stat_path * p

    format_phase("No Guarantee", rollup2)

    # --- Phase 3: with guarantee ---
    if len(guarantee_stats) < 2:
        return '\n'.join(lines)

    valid_guarantee = [g for g in guarantee_stats if g in selected_stats]
    if len(valid_guarantee) < 2:
        return '\n'.join(lines)
    guarantee_stats = valid_guarantee[:2]

    guarantee_pool = set(collapsed_name(g) for g in guarantee_stats)

    def apply_guarantee(stat_path):
        collapsed = [collapsed_name(s) for s in stat_path]
        g_count = sum(1 for c in collapsed if c in guarantee_pool)
        forced_indices = []
        for i in range(len(collapsed) - 1, -1, -1):
            if g_count >= guarantee_count:
                break
            if collapsed[i] not in guarantee_pool:
                forced_indices.append(i)
                g_count += 1
        if not forced_indices:
            yield stat_path, 1.0
            return
        for combo in itertools.product(guarantee_stats, repeat=len(forced_indices)):
            new_path = list(stat_path)
            for idx, forced_stat in zip(forced_indices, combo):
                new_path[idx] = forced_stat
            yield tuple(new_path), 0.5 ** len(forced_indices)

    rollup3 = defaultdict(float)
    for stat_path in stat_outcomes:
        for new_stat_path, weight in apply_guarantee(stat_path):
            per_collapsed, per_raw = compute_marginals(new_stat_path)
            for v, p in extract_focus_dist(per_collapsed, per_raw).items():
                rollup3[v] += p_per_stat_path * weight * p

    g_label = f"{guarantee_stats[0]}/{guarantee_stats[1]}"
    format_phase(f"With {g_label} \u2265 {guarantee_count} Guarantee", rollup3)

    return '\n'.join(lines)


# --- GUI ---

def main():
    root = tk.Tk()
    root.title("Reshaping Odds Analyzer")
    root.resizable(True, True)

    # Top controls frame
    frame_top = tk.Frame(root)
    frame_top.pack(padx=10, pady=(10, 0))

    # Stat checkboxes
    frame_checks = tk.Frame(frame_top)
    frame_checks.grid(row=0, column=0, padx=(0, 15), sticky='n')

    checkbox_vars = {}
    cb_widgets = {}
    for col, (group_name, stats) in enumerate(GROUPS):
        grp = tk.LabelFrame(frame_checks, text=group_name, padx=8, pady=5)
        grp.grid(row=0, column=col, padx=6, pady=5, sticky='n')
        for s in stats:
            var = tk.BooleanVar(value=False)
            checkbox_vars[s] = var
            cb = tk.Checkbutton(grp, text=s, variable=var)
            cb.pack(anchor='w')
            cb_widgets[s] = cb

    # Right side: rolls + guarantee
    frame_right = tk.Frame(frame_top)
    frame_right.grid(row=0, column=1, sticky='n')

    # Rolls selector
    frame_rolls = tk.LabelFrame(frame_right, text="Number of Rolls", padx=8, pady=5)
    frame_rolls.pack(pady=(5, 8), fill='x')
    num_rolls_var = tk.IntVar(value=5)
    for val in (4, 5):
        tk.Radiobutton(frame_rolls, text=str(val), variable=num_rolls_var, value=val).pack(side='left', padx=4)

    # Guaranteed rolls count selector
    frame_guarantee_count = tk.LabelFrame(frame_right, text="Guaranteed Rolls", padx=8, pady=5)
    frame_guarantee_count.pack(pady=(0, 8), fill='x')
    guarantee_count_var = tk.IntVar(value=2)
    for val in (2, 3, 4):
        tk.Radiobutton(frame_guarantee_count, text=str(val), variable=guarantee_count_var, value=val).pack(side='left', padx=4)

    # Guarantee stat selector (optional)
    frame_guarantee = tk.LabelFrame(frame_right, text="Guarantee Stats (optional, pick 2)", padx=8, pady=5)
    frame_guarantee.pack(pady=(0, 5), fill='x')

    guarantee_vars = {}
    guarantee_widgets = {}

    def rebuild_guarantee_checkboxes():
        selected = [s for s in ALL_STATS if checkbox_vars[s].get()]

        for w in list(guarantee_widgets.values()):
            w.destroy()
        guarantee_widgets.clear()

        for lbl in list(guarantee_vars.keys()):
            if lbl not in selected:
                del guarantee_vars[lbl]

        for lbl in selected:
            if lbl not in guarantee_vars:
                guarantee_vars[lbl] = tk.BooleanVar(value=False)
            cb = tk.Checkbutton(frame_guarantee, text=lbl, variable=guarantee_vars[lbl],
                                command=on_guarantee_change)
            cb.pack(anchor='w')
            guarantee_widgets[lbl] = cb

        on_guarantee_change()

    def on_guarantee_change():
        selected_count = sum(v.get() for v in guarantee_vars.values())
        for lbl, v in guarantee_vars.items():
            state = 'normal' if (v.get() or selected_count < 2) else 'disabled'
            if lbl in guarantee_widgets:
                guarantee_widgets[lbl].config(state=state)

    # Base values section
    frame_bases = tk.LabelFrame(root, text="Base Values (%)", padx=8, pady=5)
    frame_bases.pack(padx=10, pady=(5, 0), fill='x')

    base_vars = {}
    base_widgets = {}
    base_sum_label = tk.Label(frame_bases, text="Sum: — / 900")
    base_sum_label.pack(anchor='w')

    def update_base_sum(*_):
        selected = [s for s in ALL_STATS if checkbox_vars[s].get()]
        total = 0
        valid = True
        for s in selected:
            try:
                v = int(base_vars[s].get())
                total += v
            except (ValueError, KeyError):
                valid = False
        if valid and selected:
            color = 'red' if total > 900 else 'black'
            base_sum_label.config(text=f"Sum: {total} / 900", fg=color)
        else:
            base_sum_label.config(text="Sum: — / 900", fg='black')

    def rebuild_base_spinboxes():
        selected = [s for s in ALL_STATS if checkbox_vars[s].get()]

        for s in list(base_vars.keys()):
            if s not in selected:
                del base_vars[s]

        for s in list(base_widgets.keys()):
            for w in base_widgets[s]:
                w.destroy()
        base_widgets.clear()

        inner = getattr(rebuild_base_spinboxes, '_inner', None)
        if inner:
            inner.destroy()
        inner = tk.Frame(frame_bases)
        inner.pack(fill='x')
        rebuild_base_spinboxes._inner = inner

        for i, s in enumerate(selected):
            if s not in base_vars:
                base_vars[s] = tk.StringVar(value='200')
            base_vars[s].trace_add('write', update_base_sum)

            row, col = divmod(i, 4)
            lbl = tk.Label(inner, text=f"{s}:")
            lbl.grid(row=row, column=col * 2, padx=(8, 2), pady=2, sticky='e')
            spb = tk.Spinbox(inner, textvariable=base_vars[s], from_=70, to=500,
                             increment=1, width=5)
            spb.grid(row=row, column=col * 2 + 1, padx=(0, 8), pady=2, sticky='w')
            base_widgets[s] = (lbl, spb)

        update_base_sum()

    # Stat weights section (combined mode only)
    frame_weights = tk.LabelFrame(root, text="Stat Weights (Combined mode only)", padx=8, pady=5)
    frame_weights.pack(padx=10, pady=(5, 0), fill='x')

    weight_vars = {}
    weight_widgets = {}

    def rebuild_weight_spinboxes():
        selected = [s for s in ALL_STATS if checkbox_vars[s].get()]

        for s in list(weight_vars.keys()):
            if s not in selected:
                del weight_vars[s]

        for s in list(weight_widgets.keys()):
            for w in weight_widgets[s]:
                w.destroy()
        weight_widgets.clear()

        inner = getattr(rebuild_weight_spinboxes, '_inner', None)
        if inner:
            inner.destroy()
        inner = tk.Frame(frame_weights)
        inner.pack(fill='x')
        rebuild_weight_spinboxes._inner = inner

        for i, s in enumerate(selected):
            if s not in weight_vars:
                weight_vars[s] = tk.StringVar(value='1.0')

            row, col = divmod(i, 4)
            lbl = tk.Label(inner, text=f"{s}:")
            lbl.grid(row=row, column=col * 2, padx=(8, 2), pady=2, sticky='e')
            spb = tk.Spinbox(inner, textvariable=weight_vars[s], from_=0.0, to=10.0,
                             increment=0.1, format='%.1f', width=5)
            spb.grid(row=row, column=col * 2 + 1, padx=(0, 8), pady=2, sticky='w')
            weight_widgets[s] = (lbl, spb)

    # Output mode + focus selector
    frame_mode_focus = tk.Frame(root)
    frame_mode_focus.pack(padx=10, pady=(5, 0), fill='x')

    frame_mode = tk.LabelFrame(frame_mode_focus, text="Output Mode", padx=8, pady=5)
    frame_mode.pack(side='left', padx=(0, 10))

    output_mode_var = tk.StringVar(value='combined')

    frame_focus_outer = tk.LabelFrame(frame_mode_focus, text="Focus Stat (Single Stat mode)", padx=8, pady=5)
    frame_focus_outer.pack(side='left', fill='x', expand=True)

    focus_listbox = tk.Listbox(frame_focus_outer, height=5, exportselection=False, width=18)
    focus_listbox.pack(side='left', fill='x')

    def rebuild_focus_options():
        focus_listbox.delete(0, tk.END)
        selected = [s for s in ALL_STATS if checkbox_vars[s].get()]
        if not selected:
            return
        # Raw stats
        for s in selected:
            focus_listbox.insert(tk.END, s)
        # Collapsed labels (only if ≥2 raw stats collapse to them)
        for lbl in sorted(set(collapsed_name(s) for s in selected if s in COLLAPSE)):
            members = [s for s in selected if collapsed_name(s) == lbl]
            if len(members) >= 2:
                focus_listbox.insert(tk.END, f"{lbl} ({'+'.join(members)})")
        if focus_listbox.size() > 0:
            focus_listbox.selection_set(0)

    def update_focus_state(*_):
        pass  # listbox is always interactive; focus stat is ignored in combined mode

    tk.Radiobutton(frame_mode, text="Combined", variable=output_mode_var,
                   value='combined', command=update_focus_state).pack(anchor='w')
    tk.Radiobutton(frame_mode, text="Single Stat", variable=output_mode_var,
                   value='single', command=update_focus_state).pack(anchor='w')

    update_focus_state()

    def on_stat_change(*_):
        selected_count = sum(v.get() for v in checkbox_vars.values())
        for s, v in checkbox_vars.items():
            state = 'normal' if (v.get() or selected_count < 4) else 'disabled'
            cb_widgets[s].config(state=state)
        rebuild_guarantee_checkboxes()
        rebuild_base_spinboxes()
        rebuild_weight_spinboxes()
        rebuild_focus_options()

    for var in checkbox_vars.values():
        var.trace_add('write', on_stat_change)

    # Run button
    def on_run():
        selected = [s for s in ALL_STATS if checkbox_vars[s].get()]
        if len(selected) != 4:
            messagebox.showwarning("Stats", "Please select exactly 4 stats.")
            return

        mode = output_mode_var.get()
        focus = None
        if mode == 'single':
            sel_idx = focus_listbox.curselection()
            if not sel_idx:
                messagebox.showwarning("Focus", "Please select a focus stat.")
                return
            focus = focus_listbox.get(sel_idx[0]).split()[0]  # "C (CR+CD)" → "C"

        g_stats = [lbl for lbl, v in guarantee_vars.items() if v.get()]

        bases = {}
        for s in selected:
            try:
                v = int(base_vars[s].get())
            except ValueError:
                messagebox.showwarning("Base Values", f"Invalid base value for {s}.")
                return
            if not (70 <= v <= 500):
                messagebox.showwarning("Base Values", f"Base for {s} must be between 70 and 500.")
                return
            bases[s] = v

        if sum(bases.values()) > 900:
            messagebox.showwarning("Base Values",
                                   f"Sum of base values is {sum(bases.values())}%, which exceeds 900%.")
            return

        weights = {}
        for s in selected:
            try:
                w = float(weight_vars[s].get())
            except (ValueError, KeyError):
                messagebox.showwarning("Weights", f"Invalid weight for {s}.")
                return
            if w < 0:
                messagebox.showwarning("Weights", f"Weight for {s} cannot be negative.")
                return
            weights[s] = w

        num_rolls = num_rolls_var.get()
        guarantee_count = guarantee_count_var.get()
        result = run_analysis(selected, num_rolls, g_stats, guarantee_count, bases, mode, focus,
                              weights)
        output_text.config(state='normal')
        output_text.delete('1.0', tk.END)
        output_text.insert('1.0', result)
        output_text.config(state='disabled')

    tk.Button(root, text="Run Analysis", command=on_run, width=20).pack(pady=5)

    # Output area
    output_text = scrolledtext.ScrolledText(
        root, width=70, height=15, state='disabled',
        font=('Courier', 10), wrap='none'
    )
    output_text.pack(padx=10, pady=(0, 10), fill='both', expand=True)

    root.mainloop()


if __name__ == '__main__':
    main()
