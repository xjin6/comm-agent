"""
Exploratory Factor Analysis (EFA) using factor_analyzer.
Outputs: factor loadings table (CSV + XLSX), scree plot, reliability (Cronbach's α).
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from factor_analyzer import FactorAnalyzer, calculate_kmo, calculate_bartlett_sphericity
from scipy.stats import chi2


def load_file(filepath: str) -> pd.DataFrame:
    if filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)


def cronbach_alpha(data: pd.DataFrame) -> float:
    n = data.shape[1]
    if n < 2:
        return float("nan")
    item_vars = data.var(axis=0, ddof=1)
    total_var = data.sum(axis=1).var(ddof=1)
    return (n / (n - 1)) * (1 - item_vars.sum() / total_var)


def run_parallel_analysis(data: pd.DataFrame, n_iter: int = 100) -> int:
    """Estimate number of factors via parallel analysis."""
    n, p = data.shape
    real_eigenvalues = np.linalg.eigvalsh(np.corrcoef(data.T))[::-1]
    random_eigenvalues = []
    for _ in range(n_iter):
        random_data = np.random.randn(n, p)
        ev = np.linalg.eigvalsh(np.corrcoef(random_data.T))[::-1]
        random_eigenvalues.append(ev)
    random_mean = np.mean(random_eigenvalues, axis=0)
    n_factors = int(np.sum(real_eigenvalues > random_mean))
    return max(1, n_factors)


def main():
    parser = argparse.ArgumentParser(description="Run EFA on survey data")
    parser.add_argument("--file", required=True)
    parser.add_argument("--vars", required=True, help="Comma-separated variable names")
    parser.add_argument("--n-factors", default="auto",
                        help="Number of factors or 'auto' for parallel analysis")
    parser.add_argument("--rotation", default="promax",
                        choices=["promax", "oblimin", "varimax", "quartimax", "none"])
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    df = load_file(args.file)
    variables = [v.strip() for v in args.vars.split(",")]
    missing_vars = [v for v in variables if v not in df.columns]
    if missing_vars:
        print(f"ERROR: Variables not found in data: {missing_vars}", file=sys.stderr)
        sys.exit(1)

    data = df[variables].dropna()
    print(f"Using {len(data)} complete cases (dropped {len(df) - len(data)} with missing data)")

    # KMO and Bartlett's
    kmo_all, kmo_model = calculate_kmo(data)
    chi_square, p_value = calculate_bartlett_sphericity(data)
    print(f"\nKMO Measure of Sampling Adequacy: {kmo_model:.3f}")
    print(f"Bartlett's Test: χ²={chi_square:.2f}, p={p_value:.4f}")
    if kmo_model < 0.6:
        print("⚠ WARNING: KMO < 0.6 — data may not be suitable for EFA")
    if p_value > 0.05:
        print("⚠ WARNING: Bartlett's test not significant — variables may be uncorrelated")

    # Determine number of factors
    if args.n_factors == "auto":
        n_factors = run_parallel_analysis(data)
        print(f"\nParallel analysis suggests {n_factors} factor(s)")
    else:
        n_factors = int(args.n_factors)

    rotation = None if args.rotation == "none" else args.rotation

    fa = FactorAnalyzer(n_factors=n_factors, rotation=rotation, method="minres")
    fa.fit(data)

    # Loadings
    loadings = pd.DataFrame(
        fa.loadings_,
        index=variables,
        columns=[f"Factor{i+1}" for i in range(n_factors)]
    )

    # Variance explained
    ev, v = fa.get_eigenvalues()
    variance = fa.get_factor_variance()
    variance_df = pd.DataFrame(
        variance,
        index=["SS Loadings", "Proportion Var", "Cumulative Var"],
        columns=[f"Factor{i+1}" for i in range(n_factors)]
    ).round(3)

    print(f"\nFACTOR LOADINGS (rotation: {args.rotation})")
    print("─" * 60)
    print(loadings.round(3).to_string())
    print(f"\nVARIANCE EXPLAINED")
    print(variance_df.to_string())

    # Reliability per factor
    print("\nCRONBACH'S ALPHA PER FACTOR")
    alphas = {}
    for i in range(n_factors):
        factor_col = f"Factor{i+1}"
        items = loadings[loadings[factor_col].abs() > 0.40].index.tolist()
        if len(items) >= 2:
            alpha = cronbach_alpha(data[items])
            alphas[factor_col] = {"Items": ", ".join(items), "α": round(alpha, 3)}
            print(f"  Factor{i+1}: α = {alpha:.3f}  ({', '.join(items)})")
        else:
            print(f"  Factor{i+1}: fewer than 2 items with loading > .40")

    # Save CSV
    loadings.round(3).to_csv(os.path.join(args.output_dir, "efa_loadings.csv"))

    # Save APA-formatted Excel
    with pd.ExcelWriter(os.path.join(args.output_dir, "efa_loadings_table.xlsx"),
                        engine="openpyxl") as writer:
        loadings_display = loadings.copy()
        # Suppress small loadings for readability
        loadings_display = loadings_display.applymap(
            lambda x: f"{x:.2f}" if abs(x) >= 0.30 else ""
        )
        loadings_display.to_excel(writer, sheet_name="Loadings")
        variance_df.to_excel(writer, sheet_name="Variance")

    # Scree plot
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(range(1, len(ev) + 1), ev, "bo-", linewidth=2, markersize=6)
    ax.axhline(y=1, color="r", linestyle="--", alpha=0.7, label="Eigenvalue = 1")
    ax.axvline(x=n_factors, color="g", linestyle="--", alpha=0.7,
               label=f"Selected factors = {n_factors}")
    ax.set_xlabel("Factor Number")
    ax.set_ylabel("Eigenvalue")
    ax.set_title("Scree Plot")
    ax.legend()
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(args.output_dir, "scree_plot.png"), dpi=150)
    plt.close()

    print(f"\nOutputs saved to: {args.output_dir}")
    print("  - efa_loadings.csv")
    print("  - efa_loadings_table.xlsx")
    print("  - scree_plot.png")


if __name__ == "__main__":
    main()
