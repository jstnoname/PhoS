import polars as pl

SOURCE_URI = "hf://datasets/ChristophSchuhmann/MS_COCO_2017_URL_TEXT/mscoco.parquet"


def test_source_connection_to_dataset() -> None:
    df = pl.scan_parquet(SOURCE_URI)
    schema = df.collect_schema()
    n_rows = df.select(pl.len()).collect().item()

    assert "URL" in schema.names()
    assert "TEXT" in schema.names()
    assert n_rows > 500_000
