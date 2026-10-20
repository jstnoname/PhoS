# dataset_translate — спека

Результат grilling-сессии: дерево решений закрыто, вопросы не открыты. Этот файл — единственный источник правды по фиче.

## Цель

Data-prep за один прогон: перевести подписи COCO на русский и опубликовать датасет `ms-coco2017-en-ru` на HF. Сплит вне скоупа: обучения нет, модель работает только на инференсе, датасет — один parquet `url, en_text, ru_text`.

## Решения

### Данные

- Источник: `hf://datasets/ChristophSchuhmann/MS_COCO_2017_URL_TEXT/mscoco.parquet`, lazy-скан polars.
- При чтении: `TEXT -> en_text`, `URL -> url`.

### Перевод

- `facebook/nllb-200-distilled-1.3B` (600M отклонена после экспериментов — проблемы качества перевода), source `eng_Latn`, target `rus_Cyrl`, fp16 (`.half()`), `BATCH_SIZE = 128`, `MAX_LENGTH = 96` (input truncation; `max_new_tokens` в `generate` не задан — дефолт generation_config).
- Дедуп по `en_text` до перевода (570281 уникальных), merge обратно после.
- Deps в main: `sentencepiece`, `datasets` (upload в Hub через `Dataset.push_to_hub`, `huggingface-hub` — транзитивно), `python-dotenv`; в dev: `pytest`.

### Лицензия

- NLLB = CC-BY-NC-4.0: модель работает только внутри фабрики данных, веса никуда не дистрибутируются (в APK едет CLIP).
- README датасета на HF: attribution COCO (CC-BY 4.0) и NLLB + рецепт воспроизведения.

### Сплит — вне скоупа

- Обучения нет (NLLB инференсится на весь COCO), сплит не снимается, колонки `split` в датасете нет.
- Утилита `train_test_split(..., over_by)` (`ml/utility/data/split.py`, протестирована, always-lazy: юники `over_by` -> `sort` -> seeded shuffle -> нарезка -> semi-join) остаётся в `utility/` — пригодится на Этапе 2 для Recall@K-эвалов.

### Артефакт

- Один parquet, схема `en_text, url, ru_text` -> залит: публичный `jstnoname/ms-coco2017-en-ru` (~44Мб), загрузка через `datasets.Dataset.push_to_hub` (repo создаётся автоматически).
- DVC-дубль на DagsHub отклонён: датасет уже живёт и версионируется на HF Hub, ссылка есть в MLflow; DVC оставить под будущие чекпоинты/экспорты (AGENTS §8).

### MLflow

- Tracking: DagsHub remote, настройки из `.env` через `python-dotenv` (поиск `.env` вверх до корня репо); без токена — локальный `mlruns/`.
- params: model, batch_size, source_lang, target_lang, source_dataset, dataset_repo, max_length, dedup; metrics: rows, unique_en_text, unique_ru_text, unique_url; `log_input(mlflow_dataset)` без `model=`.
- Имя эксперимента: `ms-coco2017-dataset-en-ru-translate`.

### Прогоны

- smoke отменён (решение автора); полный прогон — Colab (T4); локально ячейки перевода не запускать.
- Colab Secrets: `HF_TOKEN`, `MLFLOW_TRACKING_URI`, `MLFLOW_TRACKING_USERNAME`, `MLFLOW_TRACKING_PASSWORD`, `MLFLOW_S3_ENDPOINT_URL`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` -> upload.
- Финальная ячейка: визуальная проверка перевода (EN/RU head) уже на Colab.
- **Прогон завершён** (2026-10-20): датасет залит на HF, MLflow-run `7c12477510724bfba3869ae9ceea02aa` в `jstnoname/PhoS.mlflow`.

## Шаги

1. **Deps**: `uv add sentencepiece datasets python-dotenv`, `uv add --dev pytest`; в pyproject `[tool.pytest.ini_options]` с `testpaths = ["tests"]` и `pythonpath = ["."]`. Секция `[tool.ruff]` остаётся как есть.
   Done: `uv sync` проходит; в diff pyproject только добавленные позиции.
2. **Refactor**: `train_test_split` -> `ml/utility/data/split.py` (always-lazy, `over_by` для no-leak), `__init__.py` = re-export + импорт `extends` (регистрация `custom.shuffle`); отдельной функции train/val/test нет — она достигается двумя вызовами.
   Done: `from utility.data import train_test_split` работает; in-memory тест зелёный.
3. **Ноутбук**: переименовать `01_base_experiment.ipynb` -> `00_dataset_prepare.ipynb`; контур: dotenv -> скан -> дедуп -> перевод (дедуп -> перевод -> merge) -> `push_to_hub` -> MLflow -> примеры EN->RU.
    Done: ячейки переработаны; полный прогон на Colab завершён — датасет на HF, MLflow-run залогирован (см. «Прогоны»).
4. **Тесты**: `ml/tests/` — источник (реальный `hf://`, схема `URL`,`TEXT`, >500k строк) и in-memory `train_test_split`.
   Done: `uv run pytest` зелёный.
5. **Журнал**: строка в AGENTS.md, индекс экспериментов (создана вместе со спекой).
   Done: строка присутствует.

## Гейки

- `ruff check` и `uv run pytest` зелёные; JetBrains lint — без ошибок уровня `error`.
- Полный прогон на Colab — вне шагов (без smoke-гейка).
