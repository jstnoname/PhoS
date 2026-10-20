import polars as pl
import pytest

from utility.data import train_test_split

N_URLS = 80
ROWS_PER_URL = 2


@pytest.fixture
def df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "url": [f"u{i}" for i in range(N_URLS) for _ in range(ROWS_PER_URL)],
            "en_text": [f"en-{i}-{j}" for i in range(N_URLS) for j in range(ROWS_PER_URL)],
            "ru_text": [f"ru-{i}-{j}" for i in range(N_URLS) for j in range(ROWS_PER_URL)],
        }
    )


def test_plain_split_sizes(df: pl.DataFrame) -> None:
    train, test = train_test_split(df, test_size=0.2, random_state=0)

    assert train.collect().height + test.collect().height == df.height
    assert test.collect().height == int(df.height * 0.2)
    assert train.collect().height == df.height - int(df.height * 0.2)


def test_plain_split_no_row_overlap(df: pl.DataFrame) -> None:
    train, test = train_test_split(df, test_size=0.2, random_state=0)

    train_texts = set(train.collect()["en_text"])
    test_texts = set(test.collect()["en_text"])

    assert train_texts.isdisjoint(test_texts)
    assert train_texts | test_texts == set(df["en_text"])


def test_plain_split_deterministic(df: pl.DataFrame) -> None:
    train_a, test_a = train_test_split(df, test_size=0.2, random_state=42)
    train_b, test_b = train_test_split(df, test_size=0.2, random_state=42)

    assert train_a.collect().equals(train_b.collect())
    assert test_a.collect().equals(test_b.collect())


def test_plain_split_y_stays_aligned(df: pl.DataFrame) -> None:
    x = df.select("url", "en_text")
    y = df.select("ru_text")

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=0)

    for x_part, y_part in ((x_train, y_train), (x_test, y_test)):
        paired = pl.concat([x_part, y_part], how="horizontal").collect()
        assert paired["ru_text"].equals(paired["en_text"].str.replace("en-", "ru-"))


def test_over_by_no_leak(df: pl.DataFrame) -> None:
    train, test = train_test_split(df, test_size=0.25, random_state=69, over_by="url")

    train_urls = set(train.collect()["url"])
    test_urls = set(test.collect()["url"])

    assert train_urls.isdisjoint(test_urls)
    assert train_urls | test_urls == set(df["url"])


def test_over_by_neither_side_empty(df: pl.DataFrame) -> None:
    train, test = train_test_split(df, test_size=0.25, random_state=69, over_by="url")

    assert train.collect().height > 0
    assert test.collect().height > 0


def test_over_by_row_counts_preserve_all_captions(df: pl.DataFrame) -> None:
    train, test = train_test_split(df, test_size=0.25, random_state=69, over_by="url")

    assert train.collect().height + test.collect().height == df.height


def test_over_by_deterministic(df: pl.DataFrame) -> None:
    train_a, test_a = train_test_split(df, test_size=0.25, random_state=69, over_by="url")
    train_b, test_b = train_test_split(df, test_size=0.25, random_state=69, over_by="url")

    assert train_a.collect().equals(train_b.collect())
    assert test_a.collect().equals(test_b.collect())


def test_over_by_with_y_shapes_aligned(df: pl.DataFrame) -> None:
    x = df.select("url", "en_text")
    y = df.select("ru_text")

    x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.25, random_state=69, over_by="url")

    assert x_train.collect().height == y_train.collect().height
    assert x_test.collect().height == y_test.collect().height


def test_three_way_split_ratios_and_no_leak(df: pl.DataFrame) -> None:
    train, quarter = train_test_split(df, test_size=0.25, random_state=69, over_by="url")
    val, test = train_test_split(quarter, test_size=0.5, random_state=69, over_by="url")

    train_urls = set(train.collect()["url"])
    val_urls = set(val.collect()["url"])
    test_urls = set(test.collect()["url"])

    assert train_urls.isdisjoint(val_urls)
    assert train_urls.isdisjoint(test_urls)
    assert val_urls.isdisjoint(test_urls)
    assert train_urls | val_urls | test_urls == set(df["url"])

    assert len(train_urls) == 60
    assert len(val_urls) == 10
    assert len(test_urls) == 10
