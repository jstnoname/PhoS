import polars as pl


@pl.api.register_lazyframe_namespace("custom")
class LazyFrameExtend:
    def __init__(self, lf: pl.LazyFrame):
        self._lf = lf

    def shuffle(self, seed: int = 69):
        self._lf = (
            self._lf.with_row_index()
            .with_columns(custom_shuffle_rand=pl.int_range(0, pl.len()).shuffle(seed=seed))
            .sort("custom_shuffle_rand")
            .drop(["custom_shuffle_rand", "index"])
        )
        return self._lf
