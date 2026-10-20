import polars as pl
from polars import DataFrame, LazyFrame


def train_test_split(
    X: DataFrame | LazyFrame,
    y: DataFrame | LazyFrame | None = None,
    test_size: float = 0.2,
    random_state: int = 0,
    over_by: str | None = None,
) -> tuple[LazyFrame, ...]:
    """
    :param X: DF/LF of X or all data
    :param y: y or None
    :param test_size: percentage of data to be used as test set
    :param random_state: random_state
    :param over_by: column for over-by split
    :return: (X_train, X_test) | (X_train, X_test, y_train, y_test)
    """
    x_cols = X.collect_schema().names()
    y_cols = y.collect_schema().names() if y is not None else None

    df = X.lazy()
    if y is not None:
        df = pl.concat([df, y.lazy()], how="horizontal")

    if over_by is None:
        test_count = int(df.select(pl.len()).collect().item() * test_size)
        df = df.custom.shuffle(random_state)

        X = df.select(x_cols)
        if y is not None:
            y = df.select(y_cols)
            return X.slice(test_count), X.slice(0, test_count), y.slice(test_count), y.slice(0, test_count)
        return X.slice(test_count), X.slice(0, test_count)
    else:
        unique_data = df.select(over_by).unique().sort(over_by).custom.shuffle(random_state)
        test_count = int(unique_data.select(pl.len()).collect().item() * test_size)

        train_unique = unique_data.slice(test_count)
        test_unique = unique_data.slice(0, test_count)

        train = df.join(train_unique, on=over_by, how="semi")
        test = df.join(test_unique, on=over_by, how="semi")

        if y is not None:
            return train.select(x_cols), test.select(x_cols), train.select(y_cols), test.select(y_cols)
        return train.select(x_cols), test.select(x_cols)
