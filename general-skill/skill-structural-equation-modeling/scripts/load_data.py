"""
Load and inspect a survey data file (CSV or Excel).
Prints descriptive statistics, variable list, and missing data summary.
"""

import argparse
import sys
import pandas as pd
import numpy as np


def load_file(filepath: str) -> pd.DataFrame:
    if filepath.endswith((".xlsx", ".xls")):
        return pd.read_excel(filepath)
    return pd.read_csv(filepath)


def describe(df: pd.DataFrame) -> None:
    print(f"\n{'='*60}")
    print(f"DATASET OVERVIEW")
    print(f"{'='*60}")
    print(f"Rows (respondents): {len(df)}")
    print(f"Columns (variables): {len(df.columns)}")

    print(f"\n{'─'*60}")
    print("VARIABLES")
    print(f"{'─'*60}")
    for i, col in enumerate(df.columns, 1):
        dtype = "numeric" if pd.api.types.is_numeric_dtype(df[col]) else "text"
        print(f"  {i:3}. {col}  [{dtype}]")

    print(f"\n{'─'*60}")
    print("MISSING DATA")
    print(f"{'─'*60}")
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(1)
    missing_df = pd.DataFrame({"Missing N": missing, "Missing %": missing_pct})
    missing_df = missing_df[missing_df["Missing N"] > 0]
    if missing_df.empty:
        print("  No missing data.")
    else:
        print(missing_df.to_string())
        high_missing = missing_df[missing_df["Missing %"] > 20]
        if not high_missing.empty:
            print(f"\n  ⚠ WARNING: {len(high_missing)} variable(s) exceed 20% missing:")
            for col in high_missing.index:
                print(f"    - {col}: {missing_pct[col]}%")

    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        print(f"\n{'─'*60}")
        print("DESCRIPTIVE STATISTICS (numeric variables)")
        print(f"{'─'*60}")
        desc = df[numeric_cols].describe().T[["count", "mean", "std", "min", "max"]]
        desc.columns = ["N", "Mean", "SD", "Min", "Max"]
        desc = desc.round(2)
        print(desc.to_string())

    print(f"\n{'='*60}\n")


def main():
    parser = argparse.ArgumentParser(description="Load and inspect survey data")
    parser.add_argument("--file", required=True, help="Path to CSV or Excel file")
    args = parser.parse_args()

    try:
        df = load_file(args.file)
    except FileNotFoundError:
        print(f"ERROR: File not found: {args.file}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR loading file: {e}", file=sys.stderr)
        sys.exit(1)

    describe(df)


if __name__ == "__main__":
    main()
