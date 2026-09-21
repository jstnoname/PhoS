---
name: phos-offline-check
description: Check PhoS Android offline build and search path. Use ONLY when verifying APK assets, Room vectors, or no-network search in app/.
---

# PhoS Offline Check

Контекст: `AGENTS.md` разделы 3 (п.3, п.6), 5, 7. Вариант А: модель внутри APK, 100% офлайн.

## Когда использовать
Только когда пользователь просит: проверить офлайн-сборку, `assets/`, Room-миграцию, отсутствие сети в поиске.

## Шаги
1. Проверь `app/src/main/assets/` содержит `model.onnx + tokenizer.json + model_card.json`. Версия в `model_card.json` совпадает с `ml/artifacts/model_card.json`.
2. Проверь `vector_dim` из `model_card.json` совпадает с Room entity (`embedding BLOB` размер) и кодом `OnnxEmbedder`. Несовпадение = требовать миграцию, не чинить молча.
3. Проверь поисковый путь `SearchPhotosUseCase`: embedding текста -> cosine similarity -> top-N. Никаких `http`, `Retrofit`, `OkHttp`, OpenAI/Gemini вызовов.
4. Проверь пермишены и сторедж: `READ_MEDIA_IMAGES` (Android 13+), SAF, `LazyVerticalGrid + Coil`, индексация через `WorkManager`.
5. Запусти `jetbrains_lint_files` для измененных Kotlin-файлов, затем `jetbrains_build_project`. Разбери все `errors`. Без чистого `error`-уровня задачу не закрывать.
6. Напомни: APK v1 должен работать в авиарежиме.

## Запрещено
- Предлагать докачку модели как замену встроенной (Вариант Б — только как апдейт v1.1).
- Создавать `app/back/`, `app/front/`, `shared/`.
