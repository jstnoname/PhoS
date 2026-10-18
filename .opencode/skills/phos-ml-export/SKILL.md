---
name: phos-ml-export
description: Export CLIP/SigLIP to ONNX for PhoS Android offline search. Use ONLY when exporting, quantizing, or versioning the model in ml/artifacts.
---

# PhoS ML Export

Контекст: `AGENTS.md` ADR-2/ADR-3/ADR-4. Python — фабрика моделей, на телефон едет только `.onnx`. Источник правды — `ml/artifacts/`.

## Когда использовать
Только когда пользователь просит: экспорт в ONNX, квантование, обновление `model_card.json`, перенос модели в `app/src/main/assets/`.

## Шаги
1. Сверься с `AGENTS.md` разделы 4 и 6 (кандидаты: TinyCLIP, M-CLIP, MobileSigLIP).
2. Экспорт: `torch -> onnx (opset 17) -> quantize dynamic INT8` через `ml/utility/export_onnx.py`.
3. Проверь связку из 3 файлов в `ml/artifacts/`: `model.onnx + tokenizer.json + model_card.json {model_name, version, vector_dim, tokenizer_hash}`.
4. CPU smoke-check: загрузить `.onnx` через ONNX Runtime на CPU, прогнать 1 текст RU + 1 текст EN + 1 dummy image.
5. Любое изменение `vector_dim` или токенизатора = bump `version` в `model_card.json` + напомнить про миграцию Room в `app/`.
6. Скопируй артефакт в `app/src/main/assets/` через `ml/scripts/export_to_app.py`. MLflow SDK в `app/` не тащить.
7. Цель размера: 40-60Мб, чтобы APK влез в 150Мб. Если больше — предложить меньшую модель или stronger quant.
8. После изменений: `jetbrains_lint_files` для touched Python-файлов, ошибки `error` — чинить сразу.

## Запрещено
- Добавлять облачные API в прод-путь.
- Класть Python-рантайм в `app/`.
- Создавать `shared/` — его нет по ADR-2.
