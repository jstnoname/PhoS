import polars as pl
from polars import DataFrame, LazyFrame


def train_test_split(
        X: DataFrame | LazyFrame,
        y: DataFrame | LazyFrame | None = None,
        test_size: float = 0.2,
        random_state: int = 0
) -> tuple[DataFrame | LazyFrame, ...]:
    x_cols = X.collect_schema().names()
    y_cols = y.collect_schema().names() if y is not None else None
    is_lazy = isinstance(X, LazyFrame) if y is None else (isinstance(X, LazyFrame) and isinstance(y, LazyFrame))

    df = X.lazy()
    if y is not None:
        df = pl.concat([df, y.lazy()], how='horizontal')

    test_count = int(df.select(pl.len()).collect().item() * test_size)
    df = df \
        .with_row_index() \
        .with_columns(rand=pl.int_range(0, pl.len()).shuffle(seed=random_state)) \
        .sort("rand") \
        .drop(["rand", "index"])

    if not is_lazy:
        df = df.collect()

    X = df.select(x_cols)
    if y is not None:
        y = df.select(y_cols)
        return X.slice(test_count), X.slice(0, test_count), y.slice(test_count), y.slice(0, test_count)
    return X.slice(test_count), X.slice(0, test_count)
