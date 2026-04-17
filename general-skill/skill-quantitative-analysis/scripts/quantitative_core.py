"""
clustering_core.py — Reusable Python module for survey-based clustering analysis.

Supports mixed-type survey data (numerical Likert scales + categorical variables).
Provides auto-detection of variable types, encoding, clustering (K-means, K-modes,
K-prototypes), optimal K diagnostics, and statistical analysis (ANOVA, Tukey HSD,
chi-squared, regression).

Usage:
    from clustering_core import *

Requirements:
    Install all dependencies with:
        pip install -r requirements.txt

    Or manually:
        pip install pandas numpy scipy matplotlib scikit-learn kmodes
        pip install statsmodels pingouin openpyxl

    Optional (Intel CPU acceleration for K-means):
        pip install scikit-learn-intelex
"""

import re
import os
import pickle
import numpy as np
import pandas as pd
from collections import Counter

import scipy.stats
from scipy import stats

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

from sklearn.cluster import KMeans
from sklearn.preprocessing import MinMaxScaler, MultiLabelBinarizer
from sklearn.metrics import davies_bouldin_score, silhouette_score

from kmodes.kmodes import KModes
from kmodes.kprototypes import KPrototypes

import pingouin as pg
import statsmodels.api as sm
from statsmodels.formula.api import ols
from statsmodels.stats.multicomp import pairwise_tukeyhsd

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Optional: Intel sklearn acceleration
try:
    from sklearnex import patch_sklearn
    patch_sklearn()
except ImportError:
    pass


# =============================================================================
# CONSTANTS — Likert Mapping Dictionaries
# =============================================================================

LIKERT_FREQUENCY_MAP = {
    'never': 0,
    'rarely': 1, 'seldom': 1,
    'quarterly': 2, 'sometimes': 2, 'occasionally': 2,
    'monthly': 3, 'often': 3, 'frequently': 3,
    'weekly': 4, 'regularly': 4,
    'daily': 5, 'always': 5,
}

LIKERT_IMPORTANCE_MAP = {
    'not important at all': 1, 'not important': 1, 'not at all important': 1,
    'slightly important': 2, 'a little important': 2,
    'moderately important': 3, 'somewhat important': 3,
    'very important': 4, 'important': 4,
    'extremely important': 5,
}

LIKERT_AGREEMENT_MAP = {
    'strongly disagree': 1,
    'disagree': 2,
    'neither agree nor disagree': 3, 'neutral': 3,
    'agree': 4,
    'strongly agree': 5,
}

LIKERT_SATISFACTION_MAP = {
    'very dissatisfied': 1,
    'dissatisfied': 2,
    'neither satisfied nor dissatisfied': 3, 'neutral': 3,
    'satisfied': 4,
    'very satisfied': 5,
}

LIKERT_MAPS = {
    'likert_frequency': LIKERT_FREQUENCY_MAP,
    'likert_importance': LIKERT_IMPORTANCE_MAP,
    'likert_agreement': LIKERT_AGREEMENT_MAP,
    'likert_satisfaction': LIKERT_SATISFACTION_MAP,
}

# Known Likert value sets (lowercase) for detection
_FREQUENCY_VALUES = {'never', 'rarely', 'seldom', 'quarterly', 'sometimes',
                     'occasionally', 'monthly', 'often', 'frequently',
                     'weekly', 'regularly', 'daily', 'always'}
_IMPORTANCE_VALUES = {'not important at all', 'not important', 'not at all important',
                      'slightly important', 'a little important',
                      'moderately important', 'somewhat important',
                      'very important', 'important', 'extremely important'}
_AGREEMENT_VALUES = {'strongly disagree', 'disagree',
                     'neither agree nor disagree', 'neutral',
                     'agree', 'strongly agree'}
_SATISFACTION_VALUES = {'very dissatisfied', 'dissatisfied',
                        'neither satisfied nor dissatisfied', 'neutral',
                        'satisfied', 'very satisfied'}

# =============================================================================
# CHINESE LIKERT MAPS (Fix 3 & 4)
# 不适用 / 都不适用 → None (NaN): respondent has no relevant experience;
# these are excluded from statistical calculations rather than treated as 0.
# =============================================================================

LIKERT_SATISFACTION_ZH_MAP = {
    '非常满意': 5, '满意': 4, '中立': 3, '不满意': 2, '非常不满意': 1,
    '不适用': None, '都不适用': None,
}
LIKERT_IMPORTANCE_ZH_MAP = {
    '非常重要': 5, '重要': 4, '中立': 3, '不重要': 2, '非常不重要': 1,
    '不适用': None, '都不适用': None,
}
LIKERT_NECESSITY_MAP = {
    '非常必要': 5, '必要': 4, '中立': 3, '不必要': 2, '完全不必要': 1,
    '不适用': None, '都不适用': None,
}
LIKERT_AGREEMENT_ZH_MAP = {
    '非常同意': 5, '同意': 4, '中立': 3, '不同意': 2, '非常不同意': 1,
    '不适用': None, '都不适用': None,
}
LIKERT_FREQUENCY_ZH_MAP = {
    '每天使用': 5, '每天': 5,
    '每周使用': 4, '每周': 4,
    '每月使用': 3, '每月': 3,
    '每个季度使用': 2, '很少使用': 1, '很少': 1, '从不': 0,
    '不适用': None, '都不适用': None,
}

# Register Chinese types in LIKERT_MAPS
LIKERT_MAPS.update({
    'likert_satisfaction_zh': LIKERT_SATISFACTION_ZH_MAP,
    'likert_importance_zh':   LIKERT_IMPORTANCE_ZH_MAP,
    'likert_necessity':       LIKERT_NECESSITY_MAP,
    'likert_agreement_zh':    LIKERT_AGREEMENT_ZH_MAP,
    'likert_frequency_zh':    LIKERT_FREQUENCY_ZH_MAP,
})

# Chinese Likert value sets (raw strings — no lowercasing needed)
_SATISFACTION_ZH_VALUES = {'非常满意', '满意', '中立', '不满意', '非常不满意'}
_IMPORTANCE_ZH_VALUES   = {'非常重要', '重要', '中立', '不重要', '非常不重要'}
_NECESSITY_VALUES       = {'非常必要', '必要', '中立', '不必要', '完全不必要'}
_AGREEMENT_ZH_VALUES    = {'非常同意', '同意', '中立', '不同意', '非常不同意'}
_FREQUENCY_ZH_VALUES    = {'每天使用', '每天', '每周使用', '每周', '每月使用', '每月',
                            '每个季度使用', '很少使用', '很少', '从不'}


# =============================================================================
# DATA LOADING
# =============================================================================

def load_data(filepath):
    """
    Load an Excel or CSV file into a DataFrame using plain pandas read.

    Returns: (df, info_dict) where info_dict contains loading metadata.
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext in ('.xlsx', '.xls'):
        df = pd.read_excel(filepath)
    elif ext == '.csv':
        df = pd.read_csv(filepath)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Use .xlsx, .xls, or .csv")

    info = {
        'filepath': filepath,
        'format': ext,
        'original_shape': df.shape,
    }

    return df, info


def apply_qualtrics_headers(df):
    """
    For Qualtrics exports: use row 0 as column headers, drop the metadata rows.
    """
    df.columns = df.iloc[0]
    df = df[1:].reset_index(drop=True)
    return df


def deduplicate_column_names(df, strategy='suffix'):
    """
    Resolve duplicate column names in a DataFrame.

    strategy='suffix'  → append _1, _2, ... to duplicate names (default)
    strategy='position' → append column index to every duplicate name

    This is needed for Qualtrics matrix questions where multiple sub-items
    share the same label (e.g. Q19 satisfaction and Q20 necessity both have
    sub-columns called '网站导航', '搜索引擎', etc.).

    Returns the DataFrame with unique column names.
    """
    if strategy == 'suffix':
        seen = {}
        new_cols = []
        for col in df.columns:
            if col in seen:
                seen[col] += 1
                new_cols.append(f'{col}_{seen[col]}')
            else:
                seen[col] = 0
                new_cols.append(col)
        df = df.copy()
        df.columns = new_cols
    elif strategy == 'position':
        counts = {}
        new_cols = []
        for i, col in enumerate(df.columns):
            count = list(df.columns).count(col)
            if count > 1:
                idx = counts.get(col, 0)
                counts[col] = idx + 1
                new_cols.append(f'{col}_{i}')
            else:
                new_cols.append(col)
        df = df.copy()
        df.columns = new_cols
    return df


def deduplicate(df, id_column=None):
    """
    Remove duplicate respondents. If id_column is provided, keep first occurrence.
    Rows where id_column is NaN are always kept.
    """
    if id_column is None:
        return df

    condition = (df[id_column].isna()) | (~df.duplicated(subset=[id_column], keep='first'))
    return df[condition].reset_index(drop=True)


# =============================================================================
# VARIABLE TYPE AUTO-DETECTION
# =============================================================================

def detect_column_type(series, column_name):
    """
    Detect the variable type of a single column.

    Returns a dict with:
        type: str — one of the supported types
        confidence: float — 0.0 to 1.0
        sample_values: list — up to 10 unique sample values
        n_unique: int
        suggested_mapping: dict or None
        reasoning: str
    """
    clean = series.dropna()
    if len(clean) == 0:
        return {
            'type': 'empty',
            'confidence': 1.0,
            'sample_values': [],
            'n_unique': 0,
            'suggested_mapping': None,
            'reasoning': 'Column is entirely empty/NaN',
        }

    n_unique = clean.nunique()
    sample_values = clean.unique()[:10].tolist()
    col_lower = column_name.lower()

    # --- 1. Identifier detection (by column name) ---
    id_patterns = ['id', 'email', 'timestamp', 'ip address', 'responseid',
                   'recipientemail', 'recipientlastname', 'recipientfirstname',
                   'startdate', 'enddate', 'recordeddate', 'distributionchannel',
                   'userlanguage', 'externalreference']
    for pat in id_patterns:
        if pat in col_lower or col_lower == pat:
            return {
                'type': 'identifier',
                'confidence': 0.9,
                'sample_values': sample_values,
                'n_unique': n_unique,
                'suggested_mapping': None,
                'reasoning': f'Column name matches identifier pattern "{pat}"',
            }

    # --- 2. Check if values are numeric ---
    numeric_series = pd.to_numeric(clean, errors='coerce')
    numeric_ratio = numeric_series.notna().sum() / len(clean)

    if numeric_ratio > 0.9:
        num_clean = numeric_series.dropna()
        val_range = num_clean.max() - num_clean.min()
        n_unique_num = num_clean.nunique()

        if n_unique_num <= 7 and num_clean.min() >= 0 and num_clean.max() <= 10:
            return {
                'type': 'numerical_discrete',
                'confidence': 0.8,
                'sample_values': sorted(num_clean.unique().tolist()),
                'n_unique': n_unique_num,
                'suggested_mapping': None,
                'reasoning': f'Numeric with small range (0-{int(num_clean.max())}), {n_unique_num} unique values — likely already-encoded scale',
            }
        else:
            return {
                'type': 'numerical_continuous',
                'confidence': 0.8,
                'sample_values': sample_values,
                'n_unique': n_unique_num,
                'suggested_mapping': None,
                'reasoning': f'Numeric with range {val_range:.1f} and {n_unique_num} unique values',
            }

    # --- 3. String-based analysis ---
    str_values = clean.astype(str).str.strip()
    unique_lower = set(str_values.str.lower().unique())

    # --- 3a. Likert scale detection ---
    likert_checks = [
        ('likert_frequency', _FREQUENCY_VALUES, LIKERT_FREQUENCY_MAP),
        ('likert_importance', _IMPORTANCE_VALUES, LIKERT_IMPORTANCE_MAP),
        ('likert_agreement', _AGREEMENT_VALUES, LIKERT_AGREEMENT_MAP),
        ('likert_satisfaction', _SATISFACTION_VALUES, LIKERT_SATISFACTION_MAP),
    ]

    best_likert = None
    best_overlap = 0
    for ltype, known_vals, lmap in likert_checks:
        overlap = len(unique_lower & known_vals)
        overlap_ratio = overlap / max(len(unique_lower), 1)
        if overlap_ratio > best_overlap and overlap_ratio >= 0.5:
            best_overlap = overlap_ratio
            best_likert = (ltype, lmap, overlap_ratio)

    # Also check column name hints
    if 'frequency' in col_lower or 'freq' in col_lower:
        if best_likert is None or best_likert[0] != 'likert_frequency':
            overlap = len(unique_lower & _FREQUENCY_VALUES)
            if overlap >= 2:
                best_likert = ('likert_frequency', LIKERT_FREQUENCY_MAP, 0.7)

    if 'import' in col_lower:
        if best_likert is None or best_likert[0] != 'likert_importance':
            overlap = len(unique_lower & _IMPORTANCE_VALUES)
            if overlap >= 2:
                best_likert = ('likert_importance', LIKERT_IMPORTANCE_MAP, 0.7)

    if best_likert is not None:
        ltype, lmap, conf = best_likert
        return {
            'type': ltype,
            'confidence': min(conf + 0.1, 1.0),
            'sample_values': sample_values,
            'n_unique': n_unique,
            'suggested_mapping': lmap,
            'reasoning': f'{conf*100:.0f}% of unique values match known {ltype} scale',
        }

    # --- 3a-ii. Chinese Likert detection (raw strings, no lowercasing) ---
    unique_raw = set(str_values.unique())
    _NA_ZH = {'不适用', '都不适用'}
    zh_likert_checks = [
        ('likert_satisfaction_zh', _SATISFACTION_ZH_VALUES, LIKERT_SATISFACTION_ZH_MAP),
        ('likert_importance_zh',   _IMPORTANCE_ZH_VALUES,   LIKERT_IMPORTANCE_ZH_MAP),
        ('likert_necessity',       _NECESSITY_VALUES,        LIKERT_NECESSITY_MAP),
        ('likert_agreement_zh',    _AGREEMENT_ZH_VALUES,     LIKERT_AGREEMENT_ZH_MAP),
        ('likert_frequency_zh',    _FREQUENCY_ZH_VALUES,     LIKERT_FREQUENCY_ZH_MAP),
    ]
    best_zh = None
    best_zh_overlap = 0
    for ltype, known_vals, lmap in zh_likert_checks:
        content_vals = unique_raw - _NA_ZH
        overlap = len(content_vals & known_vals)
        if overlap >= 3 and overlap > best_zh_overlap:
            best_zh_overlap = overlap
            best_zh = (ltype, lmap, overlap)

    if best_zh is not None:
        ltype, lmap, overlap = best_zh
        return {
            'type': ltype,
            'confidence': 0.9,
            'sample_values': sample_values,
            'n_unique': n_unique,
            'suggested_mapping': lmap,
            'reasoning': f'{overlap} unique values match Chinese {ltype} scale',
        }

    # --- 3b. Multi-select detection (comma-separated) ---
    comma_ratio = str_values.str.contains(',', na=False).sum() / len(str_values)
    if comma_ratio > 0.15:
        return {
            'type': 'categorical_multi',
            'confidence': 0.85,
            'sample_values': sample_values[:5],
            'n_unique': n_unique,
            'suggested_mapping': None,
            'reasoning': f'{comma_ratio*100:.0f}% of values contain commas — likely multi-select',
        }

    # --- 3c. Ordinal demographic detection ---
    ordinal_patterns = [
        r'\d+\s*[-–to]+\s*\d+',  # "18-24", "25 to 34"
        r'(?:less than|more than|under|over|fewer than)\s+\d+',  # "Less than 10"
    ]
    ordinal_match_count = 0
    for val in unique_lower:
        for pat in ordinal_patterns:
            if re.search(pat, val, re.IGNORECASE):
                ordinal_match_count += 1
                break

    ordinal_name_hints = ['age', 'income', 'experience', 'seniority', 'tenure',
                          'meeting number', 'time spend', 'hours', 'years']
    name_hint_match = any(h in col_lower for h in ordinal_name_hints)

    if ordinal_match_count / max(n_unique, 1) >= 0.5 or (name_hint_match and ordinal_match_count >= 2):
        mapping = auto_generate_ordinal_mapping(clean)
        return {
            'type': 'ordinal_demographic',
            'confidence': 0.75,
            'sample_values': sample_values,
            'n_unique': n_unique,
            'suggested_mapping': mapping,
            'reasoning': f'Values match ordinal bracket patterns ({ordinal_match_count}/{n_unique} matched)',
        }

    # --- 3d. Categorical fallback ---
    if n_unique <= 30:
        return {
            'type': 'categorical_single',
            'confidence': 0.7,
            'sample_values': sample_values,
            'n_unique': n_unique,
            'suggested_mapping': None,
            'reasoning': f'{n_unique} unique string values — likely single-select categorical',
        }

    # --- 3e. Free text ---
    return {
        'type': 'free_text',
        'confidence': 0.6,
        'sample_values': sample_values[:5],
        'n_unique': n_unique,
        'suggested_mapping': None,
        'reasoning': f'{n_unique} unique string values — likely free text',
    }


def auto_generate_ordinal_mapping(series):
    """
    For ordinal demographic columns, generate a numeric mapping by extracting
    leading numbers and sorting.
    E.g., {'Less than 10 meetings': 1, '11-20 meetings': 2, ...}
    """
    unique_vals = series.dropna().unique()
    items = []

    for val in unique_vals:
        val_str = str(val).strip()
        # Try to extract the first number
        match = re.search(r'(\d+)', val_str)
        if match:
            items.append((int(match.group(1)), val_str))
        else:
            # "Less than" / "Under" → assign 0
            if re.search(r'(?:less than|under|fewer than)', val_str, re.IGNORECASE):
                items.append((0, val_str))
            # "More than" / "Over" → assign a high number
            elif re.search(r'(?:more than|over)', val_str, re.IGNORECASE):
                items.append((9999, val_str))
            else:
                items.append((5000, val_str))  # unknown, put in middle

    items.sort(key=lambda x: x[0])
    mapping = {}
    for rank, (_, val_str) in enumerate(items, start=1):
        mapping[val_str] = rank

    return mapping


def detect_all_columns(df):
    """
    Run detect_column_type on every column.
    Returns a list of dicts, each containing the column name plus detection results.
    """
    results = []
    for col in df.columns:
        detection = detect_column_type(df[col], col)
        detection['column'] = col
        results.append(detection)
    return results


def format_detection_report(detection_results):
    """
    Format the detection results as a readable table string.
    """
    rows = []
    for i, d in enumerate(detection_results):
        sample = str(d['sample_values'][:4])
        if len(sample) > 60:
            sample = sample[:57] + '...'
        rows.append({
            'idx': i,
            'column': d['column'],
            'detected_type': d['type'],
            'confidence': f"{d['confidence']:.0%}",
            'n_unique': d['n_unique'],
            'sample_values': sample,
        })

    report_df = pd.DataFrame(rows)
    return report_df.to_string(index=False)


# =============================================================================
# ENCODING FUNCTIONS
# =============================================================================

def encode_likert(series, likert_type, custom_map=None):
    """
    Map text Likert responses to numerical values.
    Case-insensitive matching with whitespace stripping.
    Unmapped values become NaN.
    """
    if custom_map is not None:
        mapping = {k.lower().strip(): v for k, v in custom_map.items()}
    else:
        mapping = LIKERT_MAPS.get(likert_type, {})

    def _map_value(val):
        if pd.isna(val):
            return np.nan
        key = str(val).lower().strip()
        result = mapping.get(key, np.nan)
        # None in map (e.g. 不适用) means "not applicable" → exclude from stats
        return np.nan if result is None else result

    return series.apply(_map_value)


def encode_multiselect(series, separator=','):
    """
    One-hot encode a multi-select column (comma-separated or custom separator).
    Returns a DataFrame with one column per unique option.
    """
    raw = series.fillna('').astype(str)
    multi_list = raw.apply(
        lambda value: [item.strip() for item in value.split(separator) if item.strip()]
        if value else []
    )

    mlb = MultiLabelBinarizer()
    encoded = pd.DataFrame(
        mlb.fit_transform(multi_list),
        columns=mlb.classes_,
        index=series.index
    )
    return encoded


def encode_ordinal(series, mapping):
    """
    Apply a custom ordinal mapping to a column.
    """
    return series.map(mapping)


def apply_all_encodings(df, type_assignments):
    """
    Apply encodings to all columns based on confirmed type assignments.

    type_assignments: dict of {column_name: {type: str, mapping: dict or None}}

    Returns: (encoded_df, multiselect_columns_expanded)
    where multiselect_columns_expanded is a dict mapping original col name
    to the list of one-hot column names created.
    """
    encoded_df = df.copy()
    multiselect_expanded = {}

    for col, config in type_assignments.items():
        col_type = config['type']
        mapping = config.get('mapping')

        if col_type in LIKERT_MAPS:
            encoded_df[col] = encode_likert(encoded_df[col], col_type, mapping)
            # NaN is intentional: unmapped values and 不适用 (N/A) are excluded from stats

        elif col_type == 'ordinal_demographic':
            if mapping:
                encoded_df[col] = encode_ordinal(encoded_df[col], mapping)

        elif col_type == 'categorical_multi':
            separator = config.get('separator', ',')
            dummy_df = encode_multiselect(encoded_df[col], separator)
            multiselect_expanded[col] = list(dummy_df.columns)
            # Drop original, add dummies
            encoded_df = encoded_df.drop(columns=[col])
            encoded_df = pd.concat([encoded_df, dummy_df], axis=1)

        elif col_type == 'categorical_single':
            encoded_df[col] = encoded_df[col].fillna('missing')

        elif col_type in ('numerical_continuous', 'numerical_discrete'):
            encoded_df[col] = pd.to_numeric(encoded_df[col], errors='coerce').fillna(0)

        # identifier and free_text columns are left as-is (usually dropped before clustering)

    return encoded_df, multiselect_expanded


# =============================================================================
# CLUSTERING PREPARATION
# =============================================================================

def prepare_clustering_input(df, numerical_columns, categorical_columns, multiselect_columns=None):
    """
    Prepare the clustering input matrix.

    Args:
        df: encoded DataFrame
        numerical_columns: list of numerical column names (will be MinMaxScaled)
        categorical_columns: list of categorical column names (single-select + one-hot from multi-select)
        multiselect_columns: optional list of one-hot column names from multi-select (treated as categorical)

    Returns:
        matrix: np.ndarray — the clustering input
        categorical_indices: list — indices of categorical columns in the matrix
        column_names: list — names of all columns in order
        scaler: fitted MinMaxScaler
    """
    if multiselect_columns is None:
        multiselect_columns = []

    all_cat_columns = list(categorical_columns) + list(multiselect_columns)

    # Scale numerical columns
    scaler = MinMaxScaler()
    if len(numerical_columns) > 0:
        df_num_scaled = pd.DataFrame(
            scaler.fit_transform(df[numerical_columns]),
            columns=numerical_columns,
            index=df.index
        )
    else:
        df_num_scaled = pd.DataFrame(index=df.index)

    # Prepare categorical columns
    if len(all_cat_columns) > 0:
        df_cat = df[all_cat_columns].fillna('missing')
        for col in all_cat_columns:
            df_cat[col] = df_cat[col].astype(str)
    else:
        df_cat = pd.DataFrame(index=df.index)

    # Concatenate
    combined = pd.concat([df_num_scaled, df_cat], axis=1)
    column_names = list(combined.columns)
    matrix = combined.values

    # Categorical indices
    n_num = len(numerical_columns)
    categorical_indices = list(range(n_num, n_num + len(all_cat_columns)))

    return matrix, categorical_indices, column_names, scaler


def select_algorithm(categorical_indices, total_columns):
    """
    Determine which clustering algorithm to use based on feature types.
    """
    if len(categorical_indices) == 0:
        return 'kmeans'
    elif len(categorical_indices) == total_columns:
        return 'kmodes'
    else:
        return 'kprototypes'


# =============================================================================
# OPTIMAL K DIAGNOSTICS
# =============================================================================

def compute_k_diagnostics(matrix, categorical_indices, algorithm,
                          k_range=range(2, 11), random_state=42, n_init=10):
    """
    Compute diagnostic metrics for each K value.

    Returns a DataFrame with columns: [k, cost, silhouette, davies_bouldin]
    """
    results = []

    for k in k_range:
        row = {'k': k, 'cost': np.nan, 'silhouette': np.nan, 'davies_bouldin': np.nan}
        try:
            if algorithm == 'kmeans':
                model = KMeans(n_clusters=k, random_state=random_state,
                               n_init=n_init, max_iter=1000)
                labels = model.fit_predict(matrix)
                row['cost'] = model.inertia_
                if len(set(labels)) > 1:
                    row['silhouette'] = silhouette_score(matrix, labels)
                    row['davies_bouldin'] = davies_bouldin_score(matrix, labels)

            elif algorithm == 'kmodes':
                model = KModes(n_clusters=k, init='Cao', random_state=random_state,
                               n_init=n_init, max_iter=1000)
                labels = model.fit_predict(matrix)
                row['cost'] = model.cost_

            elif algorithm == 'kprototypes':
                model = KPrototypes(n_clusters=k, init='Cao', random_state=random_state,
                                    n_init=n_init, max_iter=1000)
                labels = model.fit_predict(matrix, categorical=categorical_indices)
                row['cost'] = model.cost_
                # Silhouette/DB on numerical columns only
                num_indices = [i for i in range(matrix.shape[1]) if i not in categorical_indices]
                if len(num_indices) > 0 and len(set(labels)) > 1:
                    num_matrix = matrix[:, num_indices].astype(float)
                    row['silhouette'] = silhouette_score(num_matrix, labels)
                    row['davies_bouldin'] = davies_bouldin_score(num_matrix, labels)

        except Exception as e:
            row['error'] = str(e)

        results.append(row)
        print(f"  K={k}: cost={row['cost']:.2f}" if not np.isnan(row['cost']) else f"  K={k}: failed")

    return pd.DataFrame(results)


def plot_k_diagnostics(diagnostics_df, save_path):
    """
    Create a 3-panel diagnostic chart: elbow, silhouette, Davies-Bouldin.
    Saves the figure and returns the path.
    """
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    ks = diagnostics_df['k']

    # Elbow plot
    ax = axes[0]
    costs = diagnostics_df['cost']
    ax.plot(ks, costs, 'o-', color='#2563eb', linewidth=2, markersize=6)
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Cost / Inertia')
    ax.set_title('Elbow Method')
    ax.set_xticks(ks)
    ax.grid(True, alpha=0.3)

    # Silhouette plot
    ax = axes[1]
    sil = diagnostics_df['silhouette']
    if sil.notna().any():
        ax.plot(ks, sil, 'o-', color='#16a34a', linewidth=2, markersize=6)
        best_k = ks.iloc[sil.idxmax()] if sil.notna().any() else None
        if best_k is not None:
            ax.axvline(x=best_k, color='#16a34a', linestyle='--', alpha=0.5,
                       label=f'Best K={best_k}')
            ax.legend()
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Silhouette Score')
    ax.set_title('Silhouette Score (higher = better)')
    ax.set_xticks(ks)
    ax.grid(True, alpha=0.3)

    # Davies-Bouldin plot
    ax = axes[2]
    db = diagnostics_df['davies_bouldin']
    if db.notna().any():
        ax.plot(ks, db, 'o-', color='#dc2626', linewidth=2, markersize=6)
        best_k = ks.iloc[db.idxmin()] if db.notna().any() else None
        if best_k is not None:
            ax.axvline(x=best_k, color='#dc2626', linestyle='--', alpha=0.5,
                       label=f'Best K={best_k}')
            ax.legend()
    ax.set_xlabel('Number of Clusters (K)')
    ax.set_ylabel('Davies-Bouldin Index')
    ax.set_title('Davies-Bouldin Index (lower = better)')
    ax.set_xticks(ks)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight')
    plt.close()
    return save_path


# =============================================================================
# CLUSTERING EXECUTION
# =============================================================================

def run_clustering(matrix, categorical_indices, algorithm, n_clusters,
                   random_state=42, n_init=50, max_iter=1000, gamma=None):
    """
    Run the selected clustering algorithm.

    Returns: fitted model object
    """
    if algorithm == 'kmeans':
        model = KMeans(n_clusters=n_clusters, random_state=random_state,
                       n_init=n_init, max_iter=max_iter)
        model.fit(matrix)

    elif algorithm == 'kmodes':
        model = KModes(n_clusters=n_clusters, init='Cao', random_state=random_state,
                       n_init=n_init, max_iter=max_iter)
        model.fit(matrix)

    elif algorithm == 'kprototypes':
        if gamma is None:
            n_num = matrix.shape[1] - len(categorical_indices)
            n_cat = len(categorical_indices)
            gamma = 0.5 * (n_num / max(n_cat, 1))
            gamma = max(gamma, 0.1)  # floor
        model = KPrototypes(n_clusters=n_clusters, init='Cao', random_state=random_state,
                            n_init=n_init, max_iter=max_iter, gamma=gamma)
        model.fit(matrix, categorical=categorical_indices)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    return model


def assign_clusters(df, labels, include_baseline=True):
    """
    Assign cluster labels to the original DataFrame.

    Returns:
        labeled_df: DataFrame with 'cluster' column
        groups: list of DataFrames [baseline(99), g0, g1, ..., gK-1]
        group_sizes: dict of {group_label: count}
    """
    df_labeled = df.copy()
    df_labeled['cluster'] = labels

    groups = []

    if include_baseline:
        df_baseline = df.copy()
        df_baseline['cluster'] = 99
        groups.append(df_baseline)

    unique_labels = sorted(set(labels))
    for label in unique_labels:
        groups.append(df_labeled[df_labeled['cluster'] == label].copy())

    group_sizes = {99: len(df)} if include_baseline else {}
    for label in unique_labels:
        group_sizes[label] = int((labels == label).sum())

    return df_labeled, groups, group_sizes


def save_model(model, filepath):
    """Save fitted clustering model via pickle."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'wb') as f:
        pickle.dump(model, f)


def load_model(filepath):
    """Load a previously saved clustering model from pickle."""
    with open(filepath, 'rb') as f:
        return pickle.load(f)


# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

# Default colour palette for auto-assigning section colours (supports up to 8 sections)
_DEFAULT_PALETTE = [
    '#4472C4',  # Blue
    '#70AD47',  # Green
    '#ED7D31',  # Orange
    '#9B59B6',  # Purple
    '#E74C3C',  # Red
    '#1ABC9C',  # Teal
    '#F39C12',  # Gold
    '#2980B9',  # Steel Blue
]


def _lighten_hex(hex_color, factor=0.75):
    """Blend a hex colour toward white by `factor` (0 = original, 1 = white)."""
    h = hex_color.lstrip('#')
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f'#{r:02X}{g:02X}{b:02X}'


def plot_frequency_databars(df, feature_freq_cols, cluster_col='cluster',
                            section_colors=None, section_sep=' - Frequency - ',
                            max_val=5.0, title=None,
                            save_path=None, show=True):
    """
    Plot an Excel-style conditional formatting data bar table for feature frequency means.
    Works for any survey product — sections and colours are inferred from the data or supplied.

    Parameters
    ----------
    df : DataFrame with encoded frequency columns and a cluster label column.
    feature_freq_cols : list of column names to include in the table.
    cluster_col : name of the cluster label column (default 'cluster').
    section_colors : optional dict mapping section name → hex colour string, e.g.
        {'Search': '#4472C4', 'Privacy': '#70AD47'}
        If None, colours are auto-assigned from a built-in palette.
    section_sep : substring used to split column names into (section, feature).
        Default ' - Frequency - ' matches Qualtrics naming, e.g.
        'Meeting Recap - Frequency - Transcription'. Set to None to treat every
        column as its own un-grouped row under a single 'Features' section.
    max_val : maximum value of the scale (default 5.0 for 0-5 Likert frequency).
        Adjust to 7.0 for a 1-7 scale, 10.0 for NPS, etc.
    title : chart title string. Auto-generated from max_val if not provided.
    save_path : if provided, saves the figure to this path.
    show : if True, calls plt.show().
    """
    import matplotlib.pyplot as plt
    import matplotlib.patches as mpatches

    clusters = sorted(df[cluster_col].unique())
    cluster_sizes = {c: (df[cluster_col] == c).sum() for c in clusters}
    total = len(df)

    # --- Parse section / feature names from column names (preserves column order) ---
    rows = []
    sections_seen = []
    for col in feature_freq_cols:
        if section_sep and section_sep in col:
            parts = col.split(section_sep, 1)
            section = parts[0].strip().title()
            subname = parts[1].strip()
        else:
            section = 'Features'
            subname = col
        if section not in sections_seen:
            sections_seen.append(section)
        overall = round(df[col].mean(), 2)
        cluster_means = [round(df[df[cluster_col] == c][col].mean(), 2) for c in clusters]
        rows.append([section, subname, overall] + cluster_means)

    sections_order = sections_seen

    value_cols = ['Overall'] + [f'Cluster {c}' for c in clusters]
    result = pd.DataFrame(rows, columns=['Section', 'Feature'] + value_cols)

    col_headers = [f'Overall\n(n={total})'] + [f'Cluster {c}\n(n={cluster_sizes[c]})' for c in clusters]

    # --- Section colours: user-supplied or auto-assigned from palette ---
    if section_colors is None:
        sec_text = {s: _DEFAULT_PALETTE[i % len(_DEFAULT_PALETTE)]
                    for i, s in enumerate(sections_order)}
    else:
        sec_text = dict(section_colors)
        for i, s in enumerate([s for s in sections_order if s not in sec_text]):
            sec_text[s] = _DEFAULT_PALETTE[i % len(_DEFAULT_PALETTE)]
    sec_bg = {s: _lighten_hex(c) for s, c in sec_text.items()}

    section_rows = {s: result[result['Section'] == s] for s in sections_order}

    name_width = 5.5
    cell_width = 1.5
    row_height = 0.38
    header_height = 0.55
    section_header_height = 0.38
    n_data_cols = len(value_cols)

    total_rows = len(sections_order) + len(result)
    fig_width  = name_width + n_data_cols * cell_width + 0.4
    fig_height = header_height + total_rows * row_height + 0.3

    fig, ax = plt.subplots(figsize=(fig_width, fig_height))
    ax.set_xlim(0, fig_width)
    ax.set_ylim(0, fig_height)
    ax.axis('off')

    y = fig_height - 0.15

    # Header row
    h = header_height
    ax.add_patch(mpatches.FancyBboxPatch((0.05, y - h), name_width - 0.1, h,
        boxstyle='square,pad=0', fc='#404040', ec='white', lw=1, zorder=2))
    ax.text(0.15, y - h/2, 'Feature', va='center', ha='left',
            fontsize=9, fontweight='bold', color='white', zorder=3)
    for j, label in enumerate(col_headers):
        x0 = name_width + j * cell_width
        fc = '#595959' if j == 0 else '#404040'
        ax.add_patch(mpatches.FancyBboxPatch((x0, y - h), cell_width - 0.06, h,
            boxstyle='square,pad=0', fc=fc, ec='white', lw=1, zorder=2))
        ax.text(x0 + cell_width/2 - 0.03, y - h/2, label,
                va='center', ha='center', fontsize=8, fontweight='bold', color='white', zorder=3)
    y -= h

    row_idx = 0
    for section in sections_order:
        # Section header
        h = section_header_height
        fc = sec_bg.get(section, '#EEEEEE')
        total_w = name_width + n_data_cols * cell_width
        ax.add_patch(mpatches.FancyBboxPatch((0.05, y - h), total_w - 0.1, h,
            boxstyle='square,pad=0', fc=fc, ec='white', lw=1.2, zorder=2))
        ax.text(0.2, y - h/2, f'\u25b6  {section}',
                va='center', ha='left', fontsize=9.5, fontweight='bold',
                color=sec_text.get(section, '#333333'), zorder=3)
        y -= h

        bar_color = sec_text.get(section, '#888888')
        for _, row in section_rows[section].iterrows():
            h = row_height
            bg = '#F9F9F9' if row_idx % 2 == 0 else '#FFFFFF'
            total_w = name_width + n_data_cols * cell_width
            ax.add_patch(mpatches.FancyBboxPatch((0.05, y - h), total_w - 0.1, h,
                boxstyle='square,pad=0', fc=bg, ec='#E0E0E0', lw=0.5, zorder=1))
            ax.text(0.18, y - h/2, row['Feature'], va='center', ha='left',
                    fontsize=7.8, color='#222222', zorder=3)
            padding_v = h * 0.18
            bar_h = h - 2 * padding_v
            for j, vc in enumerate(value_cols):
                val = row[vc]
                x0 = name_width + j * cell_width
                cell_inner_w = cell_width - 0.06
                bar_max_w = cell_inner_w - 0.16
                bar_w = (val / max_val) * bar_max_w
                bar_x = x0 + 0.08
                bar_y = y - h + padding_v
                alpha = 0.55 if j == 0 else 0.85
                ax.add_patch(mpatches.FancyBboxPatch((bar_x, bar_y), max(bar_w, 0.01), bar_h,
                    boxstyle='square,pad=0', fc=bar_color, alpha=alpha, ec='none', zorder=2))
                txt_x = bar_x + bar_w + 0.04
                if txt_x + 0.25 > x0 + cell_inner_w:
                    txt_x = bar_x + bar_w - 0.04
                    ha, color = 'right', 'white'
                else:
                    ha, color = 'left', '#333333'
                ax.text(txt_x, y - h/2, f'{val:.2f}', va='center', ha=ha,
                        fontsize=7.5, color=color, fontweight='bold', zorder=4)
            y -= h
            row_idx += 1

    if title is None:
        title = f'Feature Frequency by Cluster  (scale: 0 \u2192 {max_val:.0f})'
    ax.set_title(title, fontsize=11, fontweight='bold', pad=10, loc='left', x=0.01)
    plt.tight_layout(pad=0.3)

    if save_path:
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
    if show:
        plt.show()
    return fig


# =============================================================================
# ANALYSIS FUNCTIONS
# =============================================================================

def _format_group_label(group, label_column):
    """Format a readable label for a grouped subset."""
    if label_column not in group.columns:
        return 'group'

    label_values = group[label_column].dropna().unique()
    if len(label_values) != 1:
        return 'mixed'

    label_value = label_values[0]
    return f"g{label_value}" if label_column == 'cluster' else str(label_value)


def numerical_comparison(groups, columns, label_column='cluster'):
    """
    Compute mean of each numerical column for each group.
    Returns a DataFrame with columns: [variable, group_1, group_2, ...]
    """
    means = []
    for group in groups:
        group_means = []
        for col in columns:
            if col in group.columns:
                group_means.append(round(np.nanmean(pd.to_numeric(group[col], errors='coerce')), 2))
            else:
                group_means.append(np.nan)
        means.append(group_means)

    result = pd.DataFrame(means).T
    group_labels = [_format_group_label(group, label_column) for group in groups]
    result.columns = group_labels
    result.insert(0, 'variable', columns)
    return result


def categorical_comparison(groups, column, separator=',', label_column='cluster'):
    """
    Compute frequency/percentage distribution of a categorical variable per group.
    Handles both single-select and multi-select (comma-separated).

    Returns a DataFrame with rows as category values and columns as group percentages.
    """
    collection = []

    for group in groups:
        if column not in group.columns:
            continue

        data = group[column].fillna('')
        f = []
        for val in data:
            val_str = str(val)
            if val_str and val_str != '' and val_str != 'nan':
                if separator is None:
                    f.append(val_str.strip())
                else:
                    for item in val_str.split(separator):
                        item = item.strip()
                        if item:
                            f.append(item)

        total = len(group[group[column].notna() & (group[column] != '')])
        counter = Counter(f)

        percentages = {}
        for name, count in counter.items():
            percentages[name] = f"{round(count / max(total, 1) * 100, 1)}%"

        label = _format_group_label(group, label_column)
        collection.append(pd.Series(percentages, name=label))

    if not collection:
        return pd.DataFrame()

    result = pd.concat(collection, axis=1).fillna('0%')
    result.index.name = 'value'
    return result.reset_index()


def run_ttest_independent(df, variable, group_column='cluster', group_a=None, group_b=None):
    """
    Run independent samples t-test between two groups.

    Args:
        df: DataFrame
        variable: numerical column to compare
        group_column: column containing group labels
        group_a, group_b: the two group labels to compare

    Returns: dict with t_statistic, p_value, significant, cohens_d, group descriptives
    """
    df_clean = df[[variable, group_column]].dropna()
    df_clean[variable] = pd.to_numeric(df_clean[variable], errors='coerce')
    df_clean = df_clean.dropna()
    df_clean = df_clean[df_clean[group_column] != 99]

    if group_a is None or group_b is None:
        groups = sorted(df_clean[group_column].unique())
        if len(groups) < 2:
            return {'error': 'Need at least 2 groups for t-test'}
        group_a, group_b = groups[0], groups[1]

    v1 = df_clean[df_clean[group_column] == group_a][variable].values
    v2 = df_clean[df_clean[group_column] == group_b][variable].values

    if len(v1) < 2 or len(v2) < 2:
        return {'error': f'Not enough observations: group {group_a} has {len(v1)}, group {group_b} has {len(v2)}'}

    t_stat, p_val = stats.ttest_ind(v1, v2)

    # Cohen's d
    pooled_std = np.sqrt(((len(v1) - 1) * np.std(v1, ddof=1)**2 + (len(v2) - 1) * np.std(v2, ddof=1)**2) / (len(v1) + len(v2) - 2))
    cohens_d = (np.mean(v1) - np.mean(v2)) / max(pooled_std, 1e-10)

    return {
        'variable': variable,
        'test': 'independent t-test',
        'group_a': group_a,
        'group_b': group_b,
        'mean_a': round(np.mean(v1), 3),
        'std_a': round(np.std(v1, ddof=1), 3),
        'n_a': len(v1),
        'mean_b': round(np.mean(v2), 3),
        'std_b': round(np.std(v2, ddof=1), 3),
        'n_b': len(v2),
        't_statistic': round(t_stat, 4),
        'p_value': round(p_val, 6),
        'significant': p_val < 0.05,
        'cohens_d': round(cohens_d, 4),
    }


def run_ttest_paired(df, variable_1, variable_2, group_filter=None, group_column='cluster'):
    """
    Run paired samples t-test between two variables (within the same respondents).

    Args:
        df: DataFrame
        variable_1: first numerical column
        variable_2: second numerical column
        group_filter: optional — only run on a specific group (e.g., 0, 1, 2)
        group_column: column containing group labels

    Returns: dict with t_statistic, p_value, significant, descriptives for both variables
    """
    df_clean = df.copy()
    if group_filter is not None:
        df_clean = df_clean[df_clean[group_column] == group_filter]

    df_clean = df_clean[[variable_1, variable_2]].dropna()
    df_clean[variable_1] = pd.to_numeric(df_clean[variable_1], errors='coerce')
    df_clean[variable_2] = pd.to_numeric(df_clean[variable_2], errors='coerce')
    df_clean = df_clean.dropna()

    if len(df_clean) < 2:
        return {'error': f'Not enough paired observations: {len(df_clean)}'}

    v1 = df_clean[variable_1].values
    v2 = df_clean[variable_2].values

    t_stat, p_val = stats.ttest_rel(v1, v2)

    # Cohen's d for paired samples
    diff = v1 - v2
    cohens_d = np.mean(diff) / max(np.std(diff, ddof=1), 1e-10)

    return {
        'test': 'paired t-test',
        'variable_1': variable_1,
        'variable_2': variable_2,
        'group_filter': group_filter,
        'mean_1': round(np.mean(v1), 3),
        'std_1': round(np.std(v1, ddof=1), 3),
        'mean_2': round(np.mean(v2), 3),
        'std_2': round(np.std(v2, ddof=1), 3),
        'n': len(v1),
        't_statistic': round(t_stat, 4),
        'p_value': round(p_val, 6),
        'significant': p_val < 0.05,
        'cohens_d': round(cohens_d, 4),
    }


def run_anova(df, variable, group_column='cluster'):
    """
    Run one-way ANOVA for a numerical variable across groups.
    Uses pingouin for detailed output including effect size (eta-squared/np2).
    Also returns group-level descriptives (mean, std, n).

    Returns: dict with anova_table, group_descriptives, f_statistic, p_value, eta_squared
    """
    df_clean = df[[variable, group_column]].dropna()
    df_clean[variable] = pd.to_numeric(df_clean[variable], errors='coerce')
    df_clean = df_clean.dropna()

    # Exclude baseline group 99
    df_clean = df_clean[df_clean[group_column] != 99]

    if df_clean[group_column].nunique() < 2:
        return {
            'variable': variable,
            'f_statistic': np.nan,
            'p_value': np.nan,
            'significant': False,
            'eta_squared': np.nan,
            'note': 'Fewer than 2 groups',
        }

    # Group descriptives (mean, std, n)
    descriptives = df_clean.groupby(group_column)[variable].agg(['mean', 'std', 'count'])
    descriptives.columns = ['mean', 'std', 'n']
    descriptives = descriptives.round(3)

    # Pingouin ANOVA column names differ slightly across versions.
    aov = pg.anova(dv=variable, between=group_column, data=df_clean, detailed=True)
    p_column = 'p_unc' if 'p_unc' in aov.columns else 'p-unc'
    effect_column = 'np2' if 'np2' in aov.columns else 'n2' if 'n2' in aov.columns else None

    f_stat = aov['F'].iloc[0]
    p_val = aov[p_column].iloc[0]
    np2 = aov[effect_column].iloc[0] if effect_column is not None else np.nan

    return {
        'variable': variable,
        'f_statistic': round(float(f_stat), 4),
        'p_value': round(float(p_val), 6),
        'significant': float(p_val) < 0.05,
        'eta_squared': round(float(np2), 4),
        'anova_table': aov,
        'group_descriptives': descriptives,
    }


def run_tukey_hsd(df, variable, group_column='cluster'):
    """
    Run Tukey HSD post-hoc test for pairwise comparisons.
    Returns a DataFrame with pairwise results.
    """
    df_clean = df[[variable, group_column]].dropna()
    df_clean[variable] = pd.to_numeric(df_clean[variable], errors='coerce')
    df_clean = df_clean.dropna()

    # Exclude baseline group 99
    df_clean = df_clean[df_clean[group_column] != 99]

    if df_clean[group_column].nunique() < 2:
        return pd.DataFrame()

    tukey = pairwise_tukeyhsd(df_clean[variable], df_clean[group_column], alpha=0.05)

    result = pd.DataFrame(data=tukey._results_table.data[1:],
                          columns=tukey._results_table.data[0])
    # Rename statsmodels 'reject' column to 'significant' for consistency
    if 'reject' in result.columns:
        result = result.rename(columns={'reject': 'significant'})
    return result


def run_chi_squared(df, variable, group_column='cluster', groups_to_compare=None):
    """
    Run chi-squared test of independence for a categorical variable across groups.

    Args:
        df: DataFrame
        variable: categorical column to test
        group_column: column containing group labels
        groups_to_compare: optional list of specific groups to compare (e.g., [0, 1] or [3, 99]).
                           If None, uses all groups except baseline 99.

    Returns: dict with chi2, p_value, cramers_v, contingency_table,
             expected_frequencies, standardized_residuals, significant_cells
    """
    df_clean = df[[variable, group_column]].dropna()

    if groups_to_compare is not None:
        df_clean = df_clean[df_clean[group_column].isin(groups_to_compare)]
    else:
        df_clean = df_clean[df_clean[group_column] != 99]

    if df_clean[group_column].nunique() < 2 or df_clean[variable].nunique() < 2:
        return {
            'variable': variable,
            'chi2': np.nan,
            'p_value': np.nan,
            'significant': False,
            'cramers_v': np.nan,
        }

    # Observed contingency table
    contingency = pd.crosstab(df_clean[variable], df_clean[group_column])
    chi2, p_val, dof, expected = scipy.stats.chi2_contingency(contingency)

    # Expected frequencies as DataFrame
    expected_df = pd.DataFrame(
        expected,
        index=contingency.index,
        columns=contingency.columns
    ).round(2)

    # Standardized residuals: (observed - expected) / sqrt(expected)
    residuals = ((contingency - expected_df) / np.sqrt(expected_df)).round(4)

    # Significant cells: |residual| > 1.96 (i.e., p < 0.05)
    significant_cells = residuals.abs() > 1.96

    # Cramer's V
    n = contingency.sum().sum()
    min_dim = min(contingency.shape[0] - 1, contingency.shape[1] - 1)
    cramers_v = np.sqrt(chi2 / (n * max(min_dim, 1)))

    return {
        'variable': variable,
        'chi2': round(chi2, 4),
        'p_value': round(p_val, 6),
        'dof': dof,
        'significant': p_val < 0.05,
        'cramers_v': round(cramers_v, 4),
        'contingency_table': contingency,
        'expected_frequencies': expected_df,
        'standardized_residuals': residuals,
        'significant_cells': significant_cells,
    }


def full_analysis_report(groups, numerical_columns, categorical_columns, df_labeled,
                         run_anova_flag=True, run_tukey_flag=True,
                         run_chi2_flag=True, run_ttest_flag=False,
                         ttest_pairs=None):
    """
    Run the analysis pipeline based on user-selected options.

    Args:
        groups: list of group DataFrames (from assign_clusters)
        numerical_columns: list of numerical column names
        categorical_columns: list of categorical column names
        df_labeled: full DataFrame with 'cluster' column
        run_anova_flag: whether to run ANOVA
        run_tukey_flag: whether to run Tukey HSD for significant ANOVA results
        run_chi2_flag: whether to run chi-squared tests
        run_ttest_flag: whether to run t-tests
        ttest_pairs: for paired t-test, list of (var1, var2) tuples; for independent, list of (var, group_a, group_b) tuples

    Returns a dict containing all requested results.
    """
    results = {}

    # 1. Numerical comparison (always included if there are numerical columns)
    if numerical_columns:
        results['numerical_means'] = numerical_comparison(groups, numerical_columns)

    # 2. ANOVA
    if run_anova_flag and numerical_columns:
        anova_results = []
        for col in numerical_columns:
            anova_results.append(run_anova(df_labeled, col))

        # Summary table (flat, for display and export)
        anova_summary = pd.DataFrame([{
            'variable': r['variable'],
            'f_statistic': r['f_statistic'],
            'p_value': r['p_value'],
            'significant': r['significant'],
            'eta_squared': r['eta_squared'],
        } for r in anova_results])
        results['anova'] = anova_summary

        # Detailed results (includes pingouin table and group descriptives)
        results['anova_detailed'] = {r['variable']: r for r in anova_results}

        # 3. Tukey HSD for significant ANOVA results
        if run_tukey_flag:
            sig_vars = [r['variable'] for r in anova_results if r.get('significant')]
            tukey_results = {}
            for var in sig_vars:
                tukey_results[var] = run_tukey_hsd(df_labeled, var)
            results['tukey_hsd'] = tukey_results

    # 4. Categorical comparisons
    if categorical_columns:
        cat_comparisons = {}
        for col in categorical_columns:
            cat_comparisons[col] = categorical_comparison(groups, col)
        results['categorical_distributions'] = cat_comparisons

    # 5. Chi-squared
    if run_chi2_flag and categorical_columns:
        chi2_results_list = []
        chi2_detailed = {}
        for col in categorical_columns:
            result = run_chi_squared(df_labeled, col)
            chi2_results_list.append({
                'variable': result['variable'],
                'chi2': result['chi2'],
                'p_value': result['p_value'],
                'dof': result.get('dof', np.nan),
                'significant': result['significant'],
                'cramers_v': result['cramers_v'],
            })
            chi2_detailed[col] = result
        results['chi_squared'] = pd.DataFrame(chi2_results_list)
        results['chi_squared_detailed'] = chi2_detailed

    # 6. T-tests
    if run_ttest_flag and ttest_pairs:
        ttest_results = []
        for pair in ttest_pairs:
            if len(pair) == 2:
                # Paired t-test: (var1, var2)
                ttest_results.append(run_ttest_paired(df_labeled, pair[0], pair[1]))
            elif len(pair) == 3:
                # Independent t-test: (var, group_a, group_b)
                ttest_results.append(run_ttest_independent(df_labeled, pair[0],
                                                           group_a=pair[1], group_b=pair[2]))
        results['ttest'] = ttest_results

    # 7. Group sizes
    results['group_sizes'] = {
        f"g{g['cluster'].unique()[0]}": len(g) for g in groups
    }

    return results


# =============================================================================
# REGRESSION
# =============================================================================

def run_linear_regression(df, dependent_var, independent_vars, group_column='cluster'):
    """
    Run OLS linear regression.

    Args:
        df: DataFrame (baseline group 99 is automatically excluded)
        dependent_var: name of the outcome column
        independent_vars: list of predictor column names

    Returns: dict with model summary, coefficients table, r_squared, f_stat, p_value
    """
    df_clean = df[df[group_column] != 99].copy() if group_column in df.columns else df.copy()
    cols_needed = [dependent_var] + independent_vars
    df_clean = df_clean[cols_needed].dropna()

    for col in cols_needed:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    df_clean = df_clean.dropna()

    if len(df_clean) < len(independent_vars) + 2:
        return {'error': f'Not enough observations ({len(df_clean)}) for {len(independent_vars)} predictors'}

    X = sm.add_constant(df_clean[independent_vars])
    y = df_clean[dependent_var]
    model = sm.OLS(y, X).fit()

    coef_df = pd.DataFrame({
        'variable': model.params.index,
        'coefficient': model.params.round(4).values,
        'std_error': model.bse.round(4).values,
        't_statistic': model.tvalues.round(4).values,
        'p_value': model.pvalues.round(6).values,
        'significant': (model.pvalues < 0.05).values,
    })

    return {
        'type': 'linear',
        'dependent_var': dependent_var,
        'independent_vars': independent_vars,
        'n_observations': int(model.nobs),
        'r_squared': round(model.rsquared, 4),
        'adj_r_squared': round(model.rsquared_adj, 4),
        'f_statistic': round(model.fvalue, 4),
        'f_p_value': round(model.f_pvalue, 6),
        'coefficients': coef_df,
        'summary': model.summary().as_text(),
    }


def run_logistic_regression(df, dependent_var, independent_vars, group_column='cluster'):
    """
    Run logistic regression (binary outcome).

    Args:
        df: DataFrame (baseline group 99 is automatically excluded)
        dependent_var: name of the binary outcome column
        independent_vars: list of predictor column names

    Returns: dict with model summary, coefficients, odds ratios, pseudo_r_squared
    """
    df_clean = df[df[group_column] != 99].copy() if group_column in df.columns else df.copy()
    cols_needed = [dependent_var] + independent_vars
    df_clean = df_clean[cols_needed].dropna()

    for col in cols_needed:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    df_clean = df_clean.dropna()

    unique_vals = df_clean[dependent_var].nunique()
    if unique_vals != 2:
        return {'error': f'Logistic regression requires a binary outcome. "{dependent_var}" has {unique_vals} unique values.'}

    if len(df_clean) < len(independent_vars) + 2:
        return {'error': f'Not enough observations ({len(df_clean)}) for {len(independent_vars)} predictors'}

    X = sm.add_constant(df_clean[independent_vars])
    y = df_clean[dependent_var]
    model = sm.Logit(y, X).fit(disp=0)

    coef_df = pd.DataFrame({
        'variable': model.params.index,
        'coefficient': model.params.round(4).values,
        'std_error': model.bse.round(4).values,
        'z_statistic': model.tvalues.round(4).values,
        'p_value': model.pvalues.round(6).values,
        'odds_ratio': np.exp(model.params).round(4).values,
        'significant': (model.pvalues < 0.05).values,
    })

    return {
        'type': 'logistic',
        'dependent_var': dependent_var,
        'independent_vars': independent_vars,
        'n_observations': int(model.nobs),
        'pseudo_r_squared': round(model.prsquared, 4),
        'log_likelihood': round(model.llf, 4),
        'aic': round(model.aic, 4),
        'bic': round(model.bic, 4),
        'coefficients': coef_df,
        'summary': model.summary().as_text(),
    }


def run_ordinal_regression(df, dependent_var, independent_vars, group_column='cluster'):
    """
    Run ordinal logistic regression (proportional odds model) for ordered outcomes.

    Args:
        df: DataFrame (baseline group 99 is automatically excluded)
        dependent_var: name of the ordinal outcome column (e.g., Likert 1-5)
        independent_vars: list of predictor column names

    Returns: dict with model summary, coefficients, p_values
    """
    try:
        from statsmodels.miscmodels.ordinal_model import OrderedModel
    except ImportError:
        return {'error': 'OrderedModel not available. Update statsmodels: pip install --upgrade statsmodels'}

    df_clean = df[df[group_column] != 99].copy() if group_column in df.columns else df.copy()
    cols_needed = [dependent_var] + independent_vars
    df_clean = df_clean[cols_needed].dropna()

    for col in cols_needed:
        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
    df_clean = df_clean.dropna()

    if len(df_clean) < len(independent_vars) + 2:
        return {'error': f'Not enough observations ({len(df_clean)}) for {len(independent_vars)} predictors'}

    X = df_clean[independent_vars]
    y = df_clean[dependent_var]

    model = OrderedModel(y, X, distr='logit').fit(method='bfgs', disp=0)

    coef_df = pd.DataFrame({
        'variable': model.params.index,
        'coefficient': model.params.round(4).values,
        'std_error': model.bse.round(4).values,
        'z_statistic': model.tvalues.round(4).values,
        'p_value': model.pvalues.round(6).values,
        'significant': (model.pvalues < 0.05).values,
    })

    return {
        'type': 'ordinal',
        'dependent_var': dependent_var,
        'independent_vars': independent_vars,
        'n_observations': int(model.nobs),
        'pseudo_r_squared': round(getattr(model, 'prsquared', 0), 4),
        'log_likelihood': round(model.llf, 4),
        'coefficients': coef_df,
        'summary': model.summary().as_text(),
    }


# =============================================================================
# TRANSLATION
# =============================================================================

def translate_to_english(df, include_values=True, batch_size=25):
    """
    Translate a DataFrame's column names (and optionally string cell values) from
    Chinese (or any language) to English using Google Translate via deep-translator.

    Parameters
    ----------
    df : pd.DataFrame
    include_values : bool
        If True, also translate unique string values in object-dtype columns.
    batch_size : int
        Number of strings to translate per API call.

    Returns
    -------
    translated_df : pd.DataFrame — copy of df with English column names and values
    col_map : dict — {original_col_name: english_col_name}
    value_maps : dict — {col_name: {original_value: english_value}} for string columns

    Raises RuntimeError if deep-translator is not installed.
    """
    try:
        from deep_translator import GoogleTranslator
    except ImportError:
        raise RuntimeError(
            "deep-translator is required for English translation. "
            "Install it with: pip install deep-translator"
        )

    def _batch_translate(strings):
        """Translate a list of strings in batches; return list of translated strings."""
        results_list = []
        for i in range(0, len(strings), batch_size):
            batch = strings[i:i + batch_size]
            translated_batch = []
            for s in batch:
                try:
                    t = GoogleTranslator(source='auto', target='en').translate(str(s))
                    translated_batch.append(t if t else str(s))
                except Exception:
                    translated_batch.append(str(s))
            results_list.extend(translated_batch)
        return results_list

    # Translate column names
    original_cols = list(df.columns)
    translated_cols = _batch_translate(original_cols)
    col_map = dict(zip(original_cols, translated_cols))

    translated_df = df.copy()
    translated_df.columns = translated_cols

    # Translate string cell values in object columns
    value_maps = {}
    if include_values:
        for orig_col, eng_col in col_map.items():
            col_series = translated_df[eng_col]
            if col_series.dtype == object:
                unique_vals = [v for v in col_series.dropna().unique() if isinstance(v, str)]
                if unique_vals:
                    translated_vals = _batch_translate(unique_vals)
                    vmap = dict(zip(unique_vals, translated_vals))
                    value_maps[eng_col] = vmap
                    translated_df[eng_col] = col_series.map(
                        lambda x: vmap.get(x, x) if isinstance(x, str) else x
                    )

    return translated_df, col_map, value_maps


def apply_column_map(df, col_map):
    """
    Rename columns in df using a {original: english} mapping produced by
    translate_to_english(). Columns not in the map are left unchanged.
    """
    return df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})


# =============================================================================
# EXPORT
# =============================================================================

def export_to_excel(results, filepath, charts=None, raw_data=None):
    """
    Export all analysis results to a multi-sheet Excel workbook.

    Parameters
    ----------
    results : dict
        Two formats supported:

        1. **Generic dict** ``{sheet_name: value}`` — used by the
           quantitative-analysis workflow. Each key becomes a sheet name
           (truncated to 31 chars, invalid chars replaced). Value types:
           - ``pd.DataFrame`` → written directly
           - ``list[dict]`` → converted to DataFrame and written
           - ``dict[str, pd.DataFrame]`` → stacked in a single sheet with
             sub-section headers
           - any other scalar / None → skipped

        2. **Legacy clustering dict** (detected by ``'group_sizes'`` key) —
           written exactly as before.

    filepath : str
        Output .xlsx path.

    charts : list[str] | None
        Paths to PNG/JPEG chart files to embed. Each chart is placed on a
        dedicated "Charts" sheet, stacked vertically.

    raw_data : pd.DataFrame | dict[str, pd.DataFrame] | None
        Raw data to include. A single DataFrame → sheet named "Raw Data".
        A dict → one sheet per key, named "Raw - <key>" (truncated to 31 chars).

    Returns the filepath.
    """
    def _safe_sheet(name):
        name = str(name)[:31]
        return re.sub(r'[\[\]\:\*\?\/\\]', '_', name)

    def _write_results(writer):
        """Write the results dict to the open writer."""
        for sheet_name, value in results.items():
            if isinstance(value, pd.DataFrame):
                if not value.empty:
                    value.to_excel(writer, sheet_name=_safe_sheet(sheet_name), index=False)
            elif isinstance(value, list) and value and isinstance(value[0], dict):
                df_val = pd.DataFrame(value)
                df_val.to_excel(writer, sheet_name=_safe_sheet(sheet_name), index=False)
            elif isinstance(value, dict):
                row_offset = 0
                for sub_name, sub_val in value.items():
                    if isinstance(sub_val, pd.DataFrame) and not sub_val.empty:
                        header_df = pd.DataFrame({'': [str(sub_name)]})
                        header_df.to_excel(
                            writer, sheet_name=_safe_sheet(sheet_name),
                            startrow=row_offset, index=False, header=False,
                        )
                        sub_val.to_excel(
                            writer, sheet_name=_safe_sheet(sheet_name),
                            startrow=row_offset + 1, index=False,
                        )
                        row_offset += len(sub_val) + 3

    def _write_raw_data(writer):
        """Write raw_data sheets."""
        if raw_data is None:
            return
        if isinstance(raw_data, pd.DataFrame):
            if not raw_data.empty:
                raw_data.to_excel(writer, sheet_name='Raw Data', index=False)
        elif isinstance(raw_data, dict):
            for topic, df_raw in raw_data.items():
                if isinstance(df_raw, pd.DataFrame) and not df_raw.empty:
                    sheet = _safe_sheet(f'Raw - {topic}')
                    df_raw.to_excel(writer, sheet_name=sheet, index=False)

    def _embed_charts(writer):
        """Embed chart images into a Charts sheet."""
        if not charts:
            return
        try:
            from openpyxl.drawing.image import Image as XLImage
        except ImportError:
            return  # openpyxl not available — skip silently

        ws = writer.book.create_sheet('Charts')
        # Each chart is ~20 rows tall at default size; start at row 1
        anchor_row = 1
        for chart_path in charts:
            if os.path.isfile(chart_path):
                try:
                    img = XLImage(chart_path)
                    # Scale to fit a reasonable width (~800px)
                    max_width_px = 800
                    if img.width > max_width_px:
                        scale = max_width_px / img.width
                        img.width = int(img.width * scale)
                        img.height = int(img.height * scale)
                    cell_ref = f'A{anchor_row}'
                    ws.add_image(img, cell_ref)
                    # Advance: each row is ~15px; leave a 2-row gap between charts
                    rows_needed = img.height // 15 + 2
                    anchor_row += rows_needed
                except Exception:
                    pass  # bad image file — skip

    # --- Generic mode ---
    if 'group_sizes' not in results:
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            _write_results(writer)
            _write_raw_data(writer)
            _embed_charts(writer)
        return filepath

    # --- Legacy clustering mode ---
    with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
        # Group sizes
        sizes_df = pd.DataFrame([results['group_sizes']]).T
        sizes_df.columns = ['count']
        sizes_df.index.name = 'group'
        sizes_df.to_excel(writer, sheet_name='Cluster Sizes')

        # Numerical means
        if 'numerical_means' in results:
            results['numerical_means'].to_excel(writer, sheet_name='Numerical Means', index=False)

        # ANOVA results
        if 'anova' in results:
            results['anova'].to_excel(writer, sheet_name='ANOVA Results', index=False)

        # Tukey HSD
        if 'tukey_hsd' in results:
            row_offset = 0
            for var, tukey_df in results['tukey_hsd'].items():
                if not tukey_df.empty:
                    # Write variable name as header
                    pd.DataFrame({'Variable': [var]}).to_excel(
                        writer, sheet_name='Tukey HSD',
                        startrow=row_offset, index=False
                    )
                    tukey_df.to_excel(
                        writer, sheet_name='Tukey HSD',
                        startrow=row_offset + 1, index=False
                    )
                    row_offset += len(tukey_df) + 3

        # Categorical distributions
        if 'categorical_distributions' in results:
            for var, dist_df in results['categorical_distributions'].items():
                if not dist_df.empty:
                    # Truncate sheet name to 31 chars (Excel limit)
                    sheet_name = var[:31] if len(var) > 31 else var
                    # Remove invalid chars for sheet names
                    sheet_name = re.sub(r'[\[\]\:\*\?\/\\]', '_', sheet_name)
                    dist_df.to_excel(writer, sheet_name=sheet_name, index=False)

        # Chi-squared summary
        if 'chi_squared' in results:
            results['chi_squared'].to_excel(writer, sheet_name='Chi-Squared Results', index=False)

        # Chi-squared detailed (residuals)
        if 'chi_squared_detailed' in results:
            row_offset = 0
            for var, detail in results['chi_squared_detailed'].items():
                if 'standardized_residuals' in detail:
                    var_label = var[:25] if len(var) > 25 else var
                    pd.DataFrame({'Variable': [var_label], 'p_value': [detail['p_value']]}).to_excel(
                        writer, sheet_name='Chi2 Residuals',
                        startrow=row_offset, index=False
                    )
                    detail['standardized_residuals'].to_excel(
                        writer, sheet_name='Chi2 Residuals',
                        startrow=row_offset + 1
                    )
                    row_offset += len(detail['standardized_residuals']) + 3

        # T-test results
        if 'ttest' in results and results['ttest']:
            ttest_df = pd.DataFrame(results['ttest'])
            ttest_df.to_excel(writer, sheet_name='T-Test Results', index=False)

        # Regression results
        if 'regression' in results:
            for i, reg in enumerate(results['regression']):
                if 'error' not in reg:
                    sheet = f"Regression {i+1}"[:31]
                    reg['coefficients'].to_excel(writer, sheet_name=sheet, index=False)

        _write_raw_data(writer)
        _embed_charts(writer)

    return filepath
