"""
SEM analysis: CFA, full SEM, mediation, and moderation.
Uses semopy for CFA/SEM/mediation, statsmodels for moderation.
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch

try:
    import semopy
    from semopy import Model, semplot
    from semopy.stats import calc_stats
except ImportError:
    print("ERROR: semopy not installed. Run: pip install semopy", file=sys.stderr)
    sys.exit(1)


def load_file(filepath: str) -> pd.DataFrame:
    if filepath.endswith((".xlsx", ".xls")):
        xl = pd.ExcelFile(filepath)
        sheet = "A1" if "A1" in xl.sheet_names else xl.sheet_names[0]
        return pd.read_excel(filepath, sheet_name=sheet)
    return pd.read_csv(filepath)


def get_stat(stats, key, default=float("nan")):
    """Safely extract a value from semopy stats DataFrame (cols=stat names, index='Value')."""
    try:
        return float(stats.loc["Value", key])
    except (KeyError, TypeError, ValueError):
        return default


def fit_indices_table(stats) -> pd.DataFrame:
    """Extract and format fit indices from semopy stats DataFrame."""
    chi2_val = get_stat(stats, "chi2")
    dof_val = get_stat(stats, "DoF")
    indices = {
        "χ²": round(chi2_val, 3),
        "df": int(dof_val) if not np.isnan(dof_val) else "—",
        "p(χ²)": round(get_stat(stats, "chi2 p-value"), 3),
        "CFI": round(get_stat(stats, "CFI"), 3),
        "TLI": round(get_stat(stats, "TLI"), 3),
        "RMSEA": round(get_stat(stats, "RMSEA"), 3),
        "AIC": round(get_stat(stats, "AIC"), 1),
        "BIC": round(get_stat(stats, "BIC"), 1),
    }
    result = pd.DataFrame(list(indices.items()), columns=["Index", "Value"])
    benchmarks = {
        "CFI": "≥ .95",
        "TLI": "≥ .95",
        "RMSEA": "≤ .06",
    }
    result["Benchmark"] = result["Index"].map(lambda x: benchmarks.get(x, ""))
    return result


def draw_amos_diagram(model: Model, params: pd.DataFrame, model_spec: str,
                      output_path: str, stats_df=None, std_ests: bool = True) -> None:
    """
    AMOS-style path diagram (pic1 layout quality):
      - Construct (oval) at top of each cluster, items (rectangles) below
      - Measurement arrows: item → construct  (AMOS convention)
      - ε circles on items showing actual standardised residual variance
      - Structural arrows: construct → construct  (bold red/grey)
      - Fit indices box in bottom-right corner
    """
    try:
        import graphviz
    except ImportError:
        print("  WARNING: graphviz Python package not installed.", file=sys.stderr)
        return

    # ── Parse model spec ──────────────────────────────────────────────────────
    latent_vars, measurement_map = [], {}
    for line in model_spec.strip().split("\n"):
        line = line.strip()
        if "=~" in line:
            lv, items_str = line.split("=~", 1)
            lv = lv.strip()
            items = [i.strip() for i in items_str.split("+")]
            latent_vars.append(lv)
            measurement_map[lv] = items
    latent_set = set(latent_vars)
    est_col = "Est. Std" if std_ests else "Estimate"

    # ── Helper lookups ────────────────────────────────────────────────────────
    def get_val(lval, rval, col=None):
        col = col or est_col
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return None
        try:
            return float(row[col].values[0])
        except (TypeError, ValueError):
            return None

    def get_p(lval, rval):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return 1.0
        try:
            return float(row["p-value"].values[0])
        except (TypeError, ValueError):
            return 1.0

    def stars(p):
        return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))

    # Standardised residual variances from ~~ rows  (Est. Std = 1 − λ²)
    error_vals = {}
    for _, row in params[params["op"] == "~~"].iterrows():
        if row["lval"] == row["rval"]:
            try:
                error_vals[row["lval"]] = round(float(row[est_col]), 3)
            except (TypeError, ValueError):
                pass

    # Structural paths between latent vars
    structural = params[
        (params["op"] == "~") &
        (params["lval"].isin(latent_set)) &
        (params["rval"].isin(latent_set))
    ]

    # SE lookup
    def get_se(lval, rval):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return None
        try:
            return float(row["Std. Err"].values[0])
        except (TypeError, ValueError, KeyError):
            return None

    def meas_label(item, lv, is_ref):
        """Label for measurement arrow: β + SE (or ref for fixed indicator)."""
        est = get_val(item, lv)
        if est is None:
            return ""
        if is_ref:
            return f"β={est:.3f}\n(ref)"
        se  = get_se(item, lv)
        p   = get_p(item, lv)
        b   = f"β={est:.3f}{stars(p)}"
        s   = f"SE={se:.3f}" if se is not None else ""
        return f"{b}\n{s}" if s else b

    def struct_label(outcome, predictor):
        """Label for structural arrow: β + SE."""
        est = get_val(outcome, predictor)
        if est is None:
            return ""
        se  = get_se(outcome, predictor)
        p   = get_p(outcome, predictor)
        b   = f"β={est:.3f}{stars(p)}"
        s   = f"SE={se:.3f}" if se is not None else ""
        return f"{b}\n{s}" if s else b

    # ── Topological sort → assign construct levels ────────────────────────────
    from collections import defaultdict, deque
    adj     = defaultdict(list)
    in_deg  = {lv: 0 for lv in latent_vars}
    for _, row in structural.iterrows():
        pred, out = row["rval"], row["lval"]
        if pred in latent_set and out in latent_set:
            adj[pred].append(out)
            in_deg[out] += 1

    level  = {lv: 0 for lv in latent_vars if in_deg[lv] == 0}
    queue  = deque(level.keys())
    while queue:
        node = queue.popleft()
        for child in adj[node]:
            level[child] = max(level.get(child, 0), level[node] + 1)
            in_deg[child] -= 1
            if in_deg[child] == 0:
                queue.append(child)
    for lv in latent_vars:          # safety net
        level.setdefault(lv, 0)

    level_groups = defaultdict(list)
    for lv in latent_vars:
        level_groups[level[lv]].append(lv)

    # ── Calculate pixel positions (neato uses inches) ─────────────────────────
    LV_H    = 3.8   # horizontal gap between constructs
    LV_V    = 4.2   # vertical gap between construct levels
    IT_DROP = 1.3   # construct → items drop
    ER_DROP = 0.65  # items → ε drop
    IT_H    = 1.2   # horizontal gap between items within a construct

    construct_pos = {}
    for lvl, nodes in sorted(level_groups.items()):
        n = len(nodes)
        xs = [-(n - 1) * LV_H / 2 + i * LV_H for i in range(n)]
        y  = -lvl * LV_V
        for node, x in zip(nodes, xs):
            construct_pos[node] = (x, y)

    item_pos = {}
    for lv, items in measurement_map.items():
        cx, cy = construct_pos[lv]
        n = len(items)
        xs = [cx - (n - 1) * IT_H / 2 + i * IT_H for i in range(n)]
        for item, x in zip(items, xs):
            item_pos[item] = (x, cy - IT_DROP)

    err_pos = {f"e_{it}": (item_pos[it][0], item_pos[it][1] - ER_DROP)
               for lv_items in measurement_map.values()
               for it in lv_items}

    # ── Build graph (neato with fixed positions) ──────────────────────────────
    dot = graphviz.Digraph(engine="neato")
    dot.attr(bgcolor="white", splines="curved", fontname="Arial",
             dpi="180", overlap="false", sep="+10")

    # Dashed cluster box per construct  +  nodes with fixed positions
    for lv, items in measurement_map.items():
        with dot.subgraph(name=f"cluster_{lv}") as c:
            c.attr(style="dashed,rounded", fillcolor="#E8F5F5",
                   color="#5F9EA0", penwidth="1.6", margin="20", label="")
            cx, cy = construct_pos[lv]
            c.node(lv, lv, shape="ellipse", style="filled",
                   fillcolor="#A8D5CF", color="#3B7A7A", penwidth="2.0",
                   width="1.7", height="0.75", fontsize="11", fontweight="bold",
                   pos=f"{cx},{cy}!")
            for item in items:
                ix, iy = item_pos[item]
                c.node(item, item, shape="box", style="filled",
                       fillcolor="white", color="#5D6D7E", penwidth="1.3",
                       width="0.90", height="0.36", fontsize="8.5",
                       pos=f"{ix},{iy}!")
                err  = f"e_{item}"
                ex, ey = err_pos[err]
                ev   = error_vals.get(item, "")
                elbl = f"ε={ev}" if ev != "" else "ε"
                c.node(err, elbl, shape="circle", style="filled",
                       fillcolor="white", color="#A8D5CF", penwidth="1.0",
                       width="0.42", height="0.42", fontsize="7.5",
                       pos=f"{ex},{ey}!")

    # ── Edges ─────────────────────────────────────────────────────────────────
    for lv, items in measurement_map.items():
        for i, item in enumerate(items):
            is_ref = (i == 0)
            err    = f"e_{item}"
            p      = get_p(item, lv) if not is_ref else 0.0

            # ε → item  (short — positions are only ER_DROP apart)
            dot.edge(err, item, arrowsize="0.45", color="#A8D5CF", penwidth="0.9")

            # cons → item  (reflective)
            lbl = meas_label(item, lv, is_ref)
            col = "#3B7A7A" if (is_ref or p < 0.05) else "#AAAAAA"
            dot.edge(lv, item, label=lbl, fontsize="7.5",
                     color=col, penwidth="1.3", fontcolor=col)

    # Structural: predictor → outcome
    for _, row in structural.iterrows():
        outcome, predictor = row["lval"], row["rval"]
        lbl = struct_label(outcome, predictor)
        p   = get_p(outcome, predictor)
        col = "#C0392B" if p < 0.05 else "#AAAAAA"
        dot.edge(predictor, outcome, label=lbl, fontsize="9",
                 color=col, penwidth="2.5", fontcolor=col, fontweight="bold")

    # ── Fit indices box ───────────────────────────────────────────────────────
    if stats_df is not None:
        try:
            chi2  = round(float(stats_df.loc["Value", "chi2"]), 2)
            df_v  = int(float(stats_df.loc["Value", "DoF"]))
            p_chi = round(float(stats_df.loc["Value", "chi2 p-value"]), 3)
            cfi   = round(float(stats_df.loc["Value", "CFI"]), 3)
            tli   = round(float(stats_df.loc["Value", "TLI"]), 3)
            rmsea = round(float(stats_df.loc["Value", "RMSEA"]), 3)
            fit_lbl = (f"Model Fit Indices\n"
                       f"χ²({df_v}) = {chi2}, p = {p_chi}\n"
                       f"CFI = {cfi}  TLI = {tli}\n"
                       f"RMSEA = {rmsea}")
            dot.node("__fit__", fit_lbl, shape="box", style="filled,rounded",
                     fillcolor="#FDFEFE", color="#566573", penwidth="1.2",
                     fontsize="10", fontname="Arial", margin="0.15",
                     rank="sink")
        except Exception:
            pass

    # ── Render ────────────────────────────────────────────────────────────────
    base = output_path.rsplit(".", 1)[0]
    fmt  = output_path.rsplit(".", 1)[-1] if "." in output_path else "png"
    try:
        dot.render(base, format=fmt, cleanup=True)
        print(f"  Path diagram saved: {output_path}")
    except Exception as e:
        print(f"  WARNING: Could not render diagram: {e}", file=sys.stderr)


def draw_structural_diagram(params: pd.DataFrame, model_spec: str,
                            output_path: str, stats_df=None,
                            std_ests: bool = True) -> None:
    """
    Clean publication-ready structural model diagram.
    Shows ONLY latent constructs (ovals) and structural paths — no items, no ε.
    This is what goes in the paper. Factor loadings are reported in a table.
    Constructs are auto-positioned by topological sort for clear left-to-right flow.
    """
    try:
        import graphviz
        from collections import defaultdict, deque
    except ImportError:
        print("  WARNING: graphviz not installed.", file=sys.stderr)
        return

    # Parse latent vars and structural paths
    latent_vars, measurement_map = [], {}
    for line in model_spec.strip().split("\n"):
        line = line.strip()
        if "=~" in line:
            lv, items_str = line.split("=~", 1)
            lv    = lv.strip()
            items = [i.strip() for i in items_str.split("+")]
            latent_vars.append(lv)
            measurement_map[lv] = items
    latent_set = set(latent_vars)
    est_col = "Est. Std" if std_ests else "Estimate"

    structural = params[
        (params["op"] == "~") &
        (params["lval"].isin(latent_set)) &
        (params["rval"].isin(latent_set))
    ]

    def get_val(lval, rval):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return None
        try:
            return float(row[est_col].values[0])
        except (TypeError, ValueError):
            return None

    def get_se(lval, rval):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return None
        try:
            return float(row["Std. Err"].values[0])
        except (TypeError, ValueError, KeyError):
            return None

    def get_p(lval, rval):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return 1.0
        try:
            return float(row["p-value"].values[0])
        except (TypeError, ValueError):
            return 1.0

    def stars(p):
        return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))

    # Topological sort → levels
    adj    = defaultdict(list)
    in_deg = {lv: 0 for lv in latent_vars}
    for _, row in structural.iterrows():
        pred, out = row["rval"], row["lval"]
        if pred in latent_set and out in latent_set:
            adj[pred].append(out)
            in_deg[out] += 1

    level = {lv: 0 for lv in latent_vars if in_deg[lv] == 0}
    queue = deque(level.keys())
    while queue:
        node = queue.popleft()
        for child in adj[node]:
            level[child] = max(level.get(child, 0), level[node] + 1)
            in_deg[child] -= 1
            if in_deg[child] == 0:
                queue.append(child)
    for lv in latent_vars:
        level.setdefault(lv, 0)

    level_groups = defaultdict(list)
    for lv in latent_vars:
        level_groups[level[lv]].append(lv)

    # Node positions: levels flow left→right, same-level nodes stack vertically
    LV_H = 4.0   # horizontal gap between levels (inches)
    LV_V = 2.2   # vertical gap between same-level nodes

    pos = {}
    for lvl, nodes in sorted(level_groups.items()):
        n  = len(nodes)
        ys = [-(n - 1) * LV_V / 2 + i * LV_V for i in range(n)]
        for node, y in zip(nodes, ys):
            pos[node] = (lvl * LV_H, y)

    # Also position fit-indices node at bottom-right
    max_x = max(x for x, y in pos.values()) + LV_H * 0.5
    min_y = min(y for x, y in pos.values()) - LV_V

    # Build graph
    dot = graphviz.Digraph(engine="neato")
    dot.attr(bgcolor="white", splines="curved", fontname="Arial",
             dpi="180", overlap="false", sep="+15")

    # Item count label inside each oval
    for lv in latent_vars:
        n_items = len(measurement_map.get(lv, []))
        lbl  = f"{lv}\n({n_items} items)"
        x, y = pos[lv]
        dot.node(lv, lbl, shape="ellipse", style="filled",
                 fillcolor="#A8D5CF", color="#3B7A7A", penwidth="2.2",
                 width="2.0", height="1.0", fontsize="12", fontweight="bold",
                 pos=f"{x},{y}!")

    # Structural paths
    for _, row in structural.iterrows():
        outcome, predictor = row["lval"], row["rval"]
        est = get_val(outcome, predictor)
        se  = get_se(outcome, predictor)
        p   = get_p(outcome, predictor)
        sig = stars(p)
        lbl = f"β={est:.3f}{sig}\nSE={se:.3f}" if (est is not None and se is not None) else ""
        col = "#C0392B" if p < 0.05 else "#AAAAAA"
        dot.edge(predictor, outcome, label=lbl, fontsize="10",
                 color=col, penwidth="2.8", fontcolor=col, fontweight="bold")

    # Fit indices
    if stats_df is not None:
        try:
            chi2  = round(float(stats_df.loc["Value", "chi2"]), 2)
            df_v  = int(float(stats_df.loc["Value", "DoF"]))
            p_chi = round(float(stats_df.loc["Value", "chi2 p-value"]), 3)
            cfi   = round(float(stats_df.loc["Value", "CFI"]), 3)
            tli   = round(float(stats_df.loc["Value", "TLI"]), 3)
            rmsea = round(float(stats_df.loc["Value", "RMSEA"]), 3)
            fit_lbl = (f"Model Fit\n"
                       f"χ²({df_v})={chi2}, p={p_chi}\n"
                       f"CFI={cfi}  TLI={tli}\n"
                       f"RMSEA={rmsea}")
            dot.node("__fit__", fit_lbl, shape="box", style="filled,rounded",
                     fillcolor="#FDFEFE", color="#566573", penwidth="1.2",
                     fontsize="10", margin="0.15",
                     pos=f"{max_x},{min_y}!")
        except Exception:
            pass

    base = output_path.rsplit(".", 1)[0]
    fmt  = output_path.rsplit(".", 1)[-1] if "." in output_path else "png"
    try:
        dot.render(base, format=fmt, cleanup=True)
        print(f"  Structural diagram saved: {output_path}")
    except Exception as e:
        print(f"  WARNING: Could not render structural diagram: {e}", file=sys.stderr)


def run_cfa(df: pd.DataFrame, model_spec: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    model = Model(model_spec)
    model.fit(df)

    params = model.inspect(std_est=True)
    stats = calc_stats(model)

    print("\nFIT INDICES")
    print("─" * 50)
    fit_df = fit_indices_table(stats)
    print(fit_df.to_string(index=False))

    print("\nPARAMETER ESTIMATES")
    print("─" * 50)
    print(params.round(3).to_string())

    # Save outputs
    params.to_excel(os.path.join(output_dir, "cfa_parameters.xlsx"), index=False)
    fit_df.to_csv(os.path.join(output_dir, "cfa_fit_indices.csv"), index=False)
    draw_amos_diagram(model, params, model_spec, os.path.join(output_dir, "cfa_path_diagram.png"), stats_df=stats)
    draw_structural_diagram(params, model_spec, os.path.join(output_dir, "cfa_structural.png"), stats_df=stats)

    print(f"\nOutputs saved to: {output_dir}")


def run_sem(df: pd.DataFrame, model_spec: str, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    model = Model(model_spec)
    model.fit(df)

    params = model.inspect(std_est=True)
    stats = calc_stats(model)

    print("\nFIT INDICES")
    print("─" * 50)
    fit_df = fit_indices_table(stats)
    print(fit_df.to_string(index=False))

    print("\nSTRUCTURAL PATH ESTIMATES")
    structural = params[params["op"] == "~"]
    print(structural.round(3).to_string())

    params.to_excel(os.path.join(output_dir, "sem_structural_paths.xlsx"), index=False)
    fit_df.to_csv(os.path.join(output_dir, "sem_fit_indices.csv"), index=False)
    draw_amos_diagram(model, params, model_spec, os.path.join(output_dir, "sem_path_diagram.png"), stats_df=stats)
    draw_structural_diagram(params, model_spec, os.path.join(output_dir, "sem_structural.png"), stats_df=stats)
    try:
        import scripts.interactive_diagram as idia
    except ImportError:
        import importlib.util, pathlib
        spec_ = importlib.util.spec_from_file_location(
            "interactive_diagram",
            pathlib.Path(__file__).parent / "interactive_diagram.py")
        idia = importlib.util.module_from_spec(spec_)
        spec_.loader.exec_module(idia)
    idia.generate(params, model_spec, os.path.join(output_dir, "sem_interactive.html"), stats_df=stats)

    print(f"\nOutputs saved to: {output_dir}")


def run_mediation(df: pd.DataFrame, x: str, m: str, y: str,
                  n_bootstrap: int, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)

    # Build mediation model in semopy syntax
    model_spec = f"""
    {m} ~ {x}
    {y} ~ {m} + {x}
    """
    model = Model(model_spec)
    model.fit(df)
    params = model.inspect(std_est=True)

    # Extract path coefficients
    a = params[(params["lval"] == m) & (params["rval"] == x)]["Estimate"].values
    b = params[(params["lval"] == y) & (params["rval"] == m)]["Estimate"].values
    c_prime = params[(params["lval"] == y) & (params["rval"] == x)]["Estimate"].values

    if len(a) == 0 or len(b) == 0:
        print("ERROR: Could not extract mediation paths", file=sys.stderr)
        return

    a_val, b_val = float(a[0]), float(b[0])
    c_prime_val = float(c_prime[0]) if len(c_prime) > 0 else float("nan")
    indirect = a_val * b_val

    # Bootstrap CI for indirect effect
    bootstrap_indirects = []
    data_vals = df[[x, m, y]].dropna().values
    n = len(data_vals)
    for _ in range(n_bootstrap):
        idx = np.random.choice(n, n, replace=True)
        boot_df = pd.DataFrame(data_vals[idx], columns=[x, m, y])
        try:
            boot_model = Model(model_spec)
            boot_model.fit(boot_df)
            boot_params = boot_model.inspect()
            ba = boot_params[(boot_params["lval"] == m) &
                             (boot_params["rval"] == x)]["Estimate"].values
            bb = boot_params[(boot_params["lval"] == y) &
                             (boot_params["rval"] == m)]["Estimate"].values
            if len(ba) > 0 and len(bb) > 0:
                bootstrap_indirects.append(float(ba[0]) * float(bb[0]))
        except Exception:
            pass

    ci_lower = np.percentile(bootstrap_indirects, 2.5)
    ci_upper = np.percentile(bootstrap_indirects, 97.5)
    significant = not (ci_lower <= 0 <= ci_upper)

    # Total effect estimate (re-run without mediator)
    direct_model = Model(f"{y} ~ {x}")
    direct_model.fit(df[[x, y]].dropna())
    direct_params = direct_model.inspect(std_est=True)
    c_total = direct_params[(direct_params["lval"] == y) &
                             (direct_params["rval"] == x)]["Estimate"].values
    c_val = float(c_total[0]) if len(c_total) > 0 else float("nan")

    print(f"\nMEDIATION RESULTS: {x} → {m} → {y}")
    print("─" * 60)
    print(f"  a path ({x} → {m}):         {a_val:.3f}")
    print(f"  b path ({m} → {y}):         {b_val:.3f}")
    print(f"  Indirect effect (a×b):       {indirect:.3f}")
    print(f"  Bootstrap 95% CI:            [{ci_lower:.3f}, {ci_upper:.3f}]")
    print(f"  Mediation supported:         {'Yes ✓' if significant else 'No ✗'}")
    print(f"  Direct effect c' ({x}→{y}): {c_prime_val:.3f}")
    print(f"  Total effect c  ({x}→{y}):  {c_val:.3f}")

    # Determine mediation type
    c_prime_row = params[(params["lval"] == y) & (params["rval"] == x)]
    try:
        c_prime_p = float(c_prime_row["p-value"].values[0]) if len(c_prime_row) > 0 else 1.0
    except (TypeError, ValueError):
        c_prime_p = 1.0
    if significant and c_prime_p > 0.05:
        med_type = "Full mediation"
    elif significant and c_prime_p <= 0.05:
        med_type = "Partial mediation"
    else:
        med_type = "No mediation"
    print(f"  Mediation type:              {med_type}")

    # Save results table
    results = pd.DataFrame([
        {"Effect": f"a: {x} → {m}", "Estimate": round(a_val, 3), "CI 95%": ""},
        {"Effect": f"b: {m} → {y}", "Estimate": round(b_val, 3), "CI 95%": ""},
        {"Effect": "Indirect (a×b)", "Estimate": round(indirect, 3),
         "CI 95%": f"[{ci_lower:.3f}, {ci_upper:.3f}]"},
        {"Effect": f"Direct c': {x} → {y}", "Estimate": round(c_prime_val, 3), "CI 95%": ""},
        {"Effect": f"Total c: {x} → {y}", "Estimate": round(c_val, 3), "CI 95%": ""},
        {"Effect": "Mediation type", "Estimate": med_type, "CI 95%": ""},
    ])
    results.to_excel(os.path.join(output_dir, "mediation_results.xlsx"), index=False)

    # AMOS-style diagram — mediation has no latent vars so draw structural only
    draw_amos_diagram(model, params, model_spec,
                      os.path.join(output_dir, "mediation_path_diagram.png"))

    print(f"\nOutputs saved to: {output_dir}")


def run_moderation(df: pd.DataFrame, x: str, w: str, y: str,
                   center: bool, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    import statsmodels.formula.api as smf

    data = df[[x, w, y]].dropna().copy()

    if center:
        data[x] = data[x] - data[x].mean()
        data[w] = data[w] - data[w].mean()
        print(f"Mean-centered {x} and {w}")

    data["XW"] = data[x] * data[w]
    formula = f"{y} ~ {x} + {w} + XW"
    result = smf.ols(formula, data=data).fit()

    print(f"\nMODERATION RESULTS: {x} × {w} → {y}")
    print("─" * 60)
    print(result.summary2().tables[1].round(3))
    print(f"\nR² = {result.rsquared:.3f}, Adj R² = {result.rsquared_adj:.3f}")
    print(f"F({int(result.df_model)}, {int(result.df_resid)}) = {result.fvalue:.3f}, "
          f"p = {result.f_pvalue:.4f}")

    interaction_p = result.pvalues.get("XW", 1.0)
    if interaction_p < 0.05:
        print(f"\n✓ Significant interaction (XW): β = {result.params['XW']:.3f}, "
              f"p = {interaction_p:.4f} — moderation supported")
    else:
        print(f"\n✗ Non-significant interaction (XW): p = {interaction_p:.4f} — "
              f"moderation not supported")

    # Simple slopes at ±1 SD and mean of W
    w_mean = 0.0 if center else data[w].mean()
    w_sd = data[w].std()
    slopes = {}
    for label, w_val in [("Low W (−1 SD)", w_mean - w_sd),
                          ("Mean W", w_mean),
                          ("High W (+1 SD)", w_mean + w_sd)]:
        slope = result.params[x] + result.params["XW"] * w_val
        slopes[label] = slope
        print(f"  Simple slope at {label}: {slope:.3f}")

    # Save regression table
    reg_table = result.summary2().tables[1].round(3)
    reg_table.to_excel(os.path.join(output_dir, "moderation_results.xlsx"))

    # Interaction plot
    x_range = np.linspace(data[x].min(), data[x].max(), 100)
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = ["#3498DB", "#2ECC71", "#E74C3C"]
    for (label, w_val), color in zip(
        [("Low W (−1 SD)", w_mean - w_sd), ("Mean W", w_mean),
         ("High W (+1 SD)", w_mean + w_sd)], colors
    ):
        y_pred = (result.params["Intercept"] +
                  result.params[x] * x_range +
                  result.params[w] * w_val +
                  result.params["XW"] * x_range * w_val)
        ax.plot(x_range, y_pred, color=color, linewidth=2, label=label)

    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.set_title(f"Interaction Plot: {x} × {w} → {y}")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "interaction_plot.png"), dpi=150)
    plt.close()

    print(f"\nOutputs saved to: {output_dir}")


def main():
    parser = argparse.ArgumentParser(description="Run SEM/CFA/mediation/moderation")
    parser.add_argument("--file", required=True)
    parser.add_argument("--model-type", required=True,
                        choices=["cfa", "sem", "mediation", "moderation"])
    parser.add_argument("--model", help="Model spec string (for cfa/sem)")
    parser.add_argument("--x", help="Predictor variable (mediation/moderation)")
    parser.add_argument("--m", help="Mediator variable")
    parser.add_argument("--w", help="Moderator variable")
    parser.add_argument("--y", help="Outcome variable")
    parser.add_argument("--bootstrap", type=int, default=5000,
                        help="Bootstrap iterations for mediation")
    parser.add_argument("--center", action="store_true",
                        help="Mean-center X and W for moderation")
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    df = load_file(args.file)

    if args.model_type == "cfa":
        if not args.model:
            print("ERROR: --model required for CFA", file=sys.stderr)
            sys.exit(1)
        run_cfa(df, args.model, args.output_dir)

    elif args.model_type == "sem":
        if not args.model:
            print("ERROR: --model required for SEM", file=sys.stderr)
            sys.exit(1)
        run_sem(df, args.model, args.output_dir)

    elif args.model_type == "mediation":
        if not all([args.x, args.m, args.y]):
            print("ERROR: --x, --m, --y required for mediation", file=sys.stderr)
            sys.exit(1)
        run_mediation(df, args.x, args.m, args.y, args.bootstrap, args.output_dir)

    elif args.model_type == "moderation":
        if not all([args.x, args.w, args.y]):
            print("ERROR: --x, --w, --y required for moderation", file=sys.stderr)
            sys.exit(1)
        run_moderation(df, args.x, args.w, args.y, args.center, args.output_dir)


if __name__ == "__main__":
    main()
