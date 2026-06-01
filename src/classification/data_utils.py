import re
from typing import Iterable, Tuple

import pandas as pd
from sklearn.model_selection import GroupShuffleSplit, train_test_split


def normalize_text(text: str) -> str:
    if text is None:
        return ""
    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def add_normalized_text(
    df: pd.DataFrame,
    text_col: str = "text",
    norm_col: str = "__norm_text",
) -> pd.DataFrame:
    if norm_col in df.columns:
        return df
    df = df.copy()
    df[norm_col] = df[text_col].fillna("").map(normalize_text)
    return df


def dedupe_dataframe(
    df: pd.DataFrame,
    text_col: str = "text",
    label_cols: Iterable[str] | None = None,
    norm_col: str = "__norm_text",
) -> Tuple[pd.DataFrame, dict]:
    df = add_normalized_text(df, text_col=text_col, norm_col=norm_col)
    conflicts = 0
    if label_cols:
        uniqueness = df.groupby(norm_col)[list(label_cols)].nunique()
        conflicts = int((uniqueness > 1).any(axis=1).sum())
    before = len(df)
    deduped = df.drop_duplicates(subset=[norm_col], keep="first").reset_index(drop=True)
    return deduped, {"dropped": before - len(deduped), "conflicts": conflicts}


def build_stratify_key(
    df: pd.DataFrame,
    label_cols: Iterable[str],
    key_col: str = "__stratify_key",
) -> pd.DataFrame:
    df = df.copy()
    key = df[list(label_cols)[0]].astype(str)
    for col in list(label_cols)[1:]:
        key = key + "||" + df[col].astype(str)
    df[key_col] = key
    return df


def split_indices(
    df: pd.DataFrame,
    test_size: float,
    seed: int,
    grouped: bool,
    group_col: str = "__norm_text",
    stratify_col: str = "__stratify_key",
) -> Tuple[Iterable[int], Iterable[int]]:
    if grouped:
        splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
        train_idx, test_idx = next(splitter.split(df, groups=df[group_col]))
    else:
        train_idx, test_idx = train_test_split(
            df.index,
            test_size=test_size,
            random_state=seed,
            stratify=df[stratify_col],
        )
    return train_idx, test_idx


def split_holdout(
    df: pd.DataFrame,
    holdout_size: float,
    seed: int,
    grouped: bool,
    group_col: str = "__norm_text",
    stratify_col: str = "__stratify_key",
) -> Tuple[pd.DataFrame, pd.DataFrame | None]:
    if holdout_size <= 0:
        return df, None
    train_idx, holdout_idx = split_indices(
        df,
        test_size=holdout_size,
        seed=seed,
        grouped=grouped,
        group_col=group_col,
        stratify_col=stratify_col,
    )
    train_df = df.loc[train_idx].reset_index(drop=True)
    holdout_df = df.loc[holdout_idx].reset_index(drop=True)
    return train_df, holdout_df
