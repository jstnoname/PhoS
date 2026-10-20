# AGENTS.md — PhoS: офлайн AI-поиск фото по описанию (RU/EN)

> Этот файл — единый источник правды по архитектуре. Агент обязан сверяться с ним перед любыми изменениями.

## 1. Идея проекта
Android-приложение: пользователь открывает папку с фотографиями, приложение фоново индексирует их, в поисковой строке вводится описание («кот на диване») — показываются наиболее релевантные фото.

Ядро поиска — семантический: модель CLIP/SigLIP превращает фото и текст в embeddings (векторы), релевантность = косинусное сходство. Не поиск по имени файла.

## 2. Цели автора (портфолио + учеба)
- Большой полноценный проект для демонстрации опыта в программировании и ML.
- Прокачать: программирование и архитектуру, Data Science + ML Engineering + MLOps, работу с большим проектом (CI/CD, зависимости, версионирование).
- Стек учебы: Kotlin + Coroutines/Flow, Jetpack Compose + MVVM + Clean, Room, ONNX Runtime Mobile, ML-основы (embeddings, токенизация, векторный поиск), Android Storage (MediaStore, SAF, Scoped Storage).
- Закладывать расширяемость: требования будут меняться.

## 3. Жёсткие ограничения (не нарушать)
1. **Платформа v1: только Android.** iOS — только как далекая опция.
2. **ML-эксперименты: 100% Python.** Автор знает только Python-библиотеки для ML.
3. **Рантайм: 100% офлайн, без интернета.** Наличие интернета для такого приложения не оправдано и оттолкнет пользователей + не должно требовать оплаты API. Следствие: никаких облачных API (OpenAI/Gemini) в прод-пути.
4. **Языки запросов: русский + английский.** Нужна мультиязычная модель.
5. **Железо автора: ноутбук без дискретной видеокарты, только Intel iGPU (XPU) + Colab/Kaggle.** Весь train/eval — на Colab/Kaggle (T4), локально только CPU-проверка экспорта.
6. **Модель обязана быть внутри APK (Вариант А).** Вариант Б (докачка при первом запуске) отклонен для v1, т.к. оставляет пользователя без модели = бесполезное приложение. Вариант Б допустим позже только как механизм обновления (v1.1), старая модель при этом продолжает работать.

## 4. Принятые архитектурные решения (ADR кратко)

### ADR-1: Kotlin Native вместо C# (.NET MAUI) и вместо Python-on-Android
- Автор знает C#, не знает Kotlin. Решение: **учить Kotlin + Jetpack Compose**.
- Почему не MAUI: хуже доступ к MediaStore/SAF/пермишенам, хуже тулинг ONNX под Android, низкая ценность для резюме, риск «костылей».
- Почему не Chaquopy/Kivy/BeeWare (Python на телефоне): APK 300Мб+, медленно, жрет батарею, слабо выглядит в портфолио.
- Kotlin учится быстро с бэкграундом C# (null-safety, coroutines ~ async/await, LINQ ~ collections).

### ADR-2: Python — фабрика моделей, а не рантайм
- Формула: `Python (Colab/Kaggle + MLflow) -> export -> model.onnx`, на телефон едет только `.onnx`.
- **Отдельной папки `shared/` нет** (отклонено как лишняя сущность). Источник правды — `ml/artifacts/`.

### ADR-3: MLflow только в `ml/`, никогда в `app/`
- MLflow = склад экспериментов и Model Registry для разработчика. Телефон в офлайне не может ходить в локальный MLflow-сервер, плюс это не CDN для Play Market.
- Цепочка поставки: `Colab train -> MLflow Registry (vX.Y.Z) -> [export скриптом] -> ml/artifacts/ -> копия в app/src/main/assets/ -> GitHub Releases -> телефон (офлайн навсегда)`.
- В `app/` нет MLflow SDK, только проверка `model_card.json` (версия, dim).

### ADR-4: Артефакт модели = связка из 3 файлов
- `model.onnx (opset 17, INT8 quantized)` + `tokenizer.json` + `model_card.json {model_name, version, vector_dim, tokenizer_hash}`.
- Метаданные нельзя хранить только внутри `.onnx`: телефону до загрузки надо знать версию/dim для проверки совместимости и миграции базы векторов в Room.
- Полный артефакт живет в `ml/artifacts/`, легкая копия `model_card.json` + сам `.onnx` копируются в `app/src/main/assets/` скриптом `ml/scripts/export_to_app.py`.

### ADR-5: Векторная БД — два уровня
- v1 на телефоне: `Room` хранит `id, uri, embedding BLOB, mtime` + brute-force cosine в Kotlin. Хватает до ~10к фото (10к*512 float ≈ 20Мб, поиск <100мс). Просто и надежно для MVP.
- v2 для учебы/портфолио: `SQLite-vss / ObjectBox` локально + `Qdrant (docker)` в `ml/` для экспериментов и бенчмарков recall/latency. Дает строчку «работал с векторными БД» без оверкилла в MVP.
- RAG — только как будущее расширение: `CLIP-поиск (retrieval) + on-device caption (BLIP/Moondream)`. В MVP не делать, но контракт не ломать.

## 5. Структура монорепо (зафиксирована)

```
PhoS/
  ml/                          # Python, source of truth для модели
    pyproject.toml (uv)        # зависимости, ruff, pytest
    utility/                   # Python-пакет (__init__.py): код для работы, напр. utility/data/ — файлы обработки данных
    experiments/               # журнал экспериментов: папки 0x_name (номер + что происходило), см. §6
    artifacts/                 # model.onnx + tokenizer.json + model_card.json
    scripts/export_to_app.py   # копирует артефакт в app/src/main/assets/
  app/                         # Android, Kotlin + Compose (НЕ back/front, а слои)
    data/                      # MediaStoreDataSource, PhotoDatabase (Room), OnnxEmbedder
    domain/                    # SearchPhotosUseCase и др.
    ui/                        # Compose: GalleryScreen, SearchBar, IndexProgress (условные templates)
    ml/                        # код инференса ONNX + проверка model_card
    src/main/assets/           # копия model.onnx + tokenizer + model_card (Вариант А)
  docs/                        # вся документация в одном месте
    architecture.md            # ссылка на этот AGENTS.md + схемы
    ml-experiments.md          # ссылки на MLflow runs
    adr/
    agents/                    # issue-tracker.md, domain.md (setup-matt-pocock-skills)
  .github/workflows/           # ci-ml.yml (ruff+pytest+export smoke), ci-app.yml (assembleDebug+unit tests)
```

Запрещено: создавать `app/back/`, `app/front/`, `shared/`, тащить Python-рантайм на телефон, добавлять сетевые вызовы в поисковый путь.

## 6. ML-ядро: кандидаты и пайплайн
Кандидаты для RU+EN офлайн (сравнить в `ml/` по Recall@5/Recall@10 RU/EN + latency CPU + размер):
1. `TinyCLIP ViT-40M` — самый легкий.
2. `Multilingual-CLIP (M-CLIP, LaBSE XLM-R)` — лучший русский из коробки, требует квантования.
3. `MobileSigLIP / SigLIP-B/16 multilingual` — фаворит, баланс точность/размер.

### Данные (v1)
- Источник: `ChristophSchuhmann/MS_COCO_2017_URL_TEXT` (591,753 подписи, `URL` + `TEXT`, ~118K изображений по URL, ~5 подписей на картинку). Чтение: `pl.read_parquet('hf://datasets/ChristophSchuhmann/MS_COCO_2017_URL_TEXT/mscoco.parquet')` — поларс с нативным `hf://`, данные не скачиваются в репо, папки `ml/data/` нет.
- Flickr30k — отложен из скоупа v1 (скриптовый лоадер мёртв в `datasets` v3, единственный сплит); вернуть можно позже как eval-бенчмарк.
- ~200 своих фото с RU/EN-подписями — Этап 4, хранение через DVC (DagsHub).

Пайплайн: датасет -> обучение/файнтюн на Kaggle/Colab -> логи в MLflow -> выбор версии -> `torch -> onnx (opset 17) -> quantize dynamic INT8` -> проверка загрузки на CPU локально.

Цель размера: ужаться до 40-60Мб, чтобы APK ~120-140Мб влез в лимит Play Market (150Мб).

Журнал экспериментов: каждый эксперимент — папка `ml/experiments/0x_name` (сквозной номер `01`, `02`... + короткое имя на латинице snake_case, что происходит). Внутри папки — ноутбук/скрипты и выходы; запуски логируются в MLflow. Индекс экспериментов ведётся в этой секции:

| № | Папка | Что происходит | Итог |
|---|-------|----------------|------|
| 00 | ml/experiments/00_dataset_prepare.ipynb | COCO -> датасет ms-coco2017-en-ru: NLLB-1.3B перевод (дедуп), без сплита | датасет: jstnoname/ms-coco2017-en-ru; MLflow->DagsHub; спека: .scratch/dataset_translate/spec.md |

## 7. Mobile v1: скоуп
- SAF выбор папки + `READ_MEDIA_IMAGES` (Android 13+), сетка `LazyVerticalGrid + Coil`.
- Фоновая индексация через `WorkManager` с прогрессом («45/300...»), инкрементальная (только новые по mtime), пропуск видео в v1.
- Поиск: embedding текста -> cosine similarity -> top-N, debounce 300мс, отображение score.
- Модель грузится из `assets/` при старте, дальше 100% офлайн.

## 8. Тулинг
- Python-зависимости: `uv + pyproject.toml` (современно, быстро). `conda` — только если понадобится CUDA локально.
- MLOps: `DagsHub` — один репозиторий = git + MLflow (params/metrics/артефакты) + DVC (крупные файлы: срезы датасетов, чекпоинты, экспорты), один эксперимент не надо собирать по кусочкам. Токен — `DAGSHUB_TOKEN` в `.env` (в `.gitignore`), на Colab — Colab Secrets. Подключение — при первом эксперименте (Этап 2). В `app/` не попадает (ADR-3).
- CI/CD: GitHub Actions, два воркфлоу (ml и app).
- Android: Gradle KTS, ONNX Runtime Mobile (`ai.onnxruntime:onnxruntime-android`), Room, WorkManager, Coil, Compose + MVVM.
- JDK: системный `java` в PATH отсутствует. Android SDK — `C:\Users\Alexander\AppData\Local\Android\Sdk`. Для сборки `app/` использовать JBR Android Studio (`C:\Users\Alexander\AppData\Local\Programs\Android Studio\jbr`, OpenJDK 25) либо отдельный JDK 17/21 с указанием `org.gradle.java.home` в `gradle.properties` (CLI-сборки).

## 9. Роадмап
- Этап 0: скелет (uv init, Compose template, Actions green).
- Этап 1: приложение без AI (папка -> сетка, поиск-заглушка по имени).
- Этап 2: ML-эксперименты в Colab (DagsHub: MLflow + DVC, сравнение моделей, выбор версии).
- Этап 3: связка (запрос RU/EN -> офлайн топ-N).
- Этап 4: MLOps и полировка (Qdrant-бенч, свои фото RU/EN через DVC, README-демо, иконка, темная тема).
- Этап 5+: captioning, фильтры, обновления модели OTA.

## 10. Правила для агента
- Перед кодом читать этот файл и `docs/`.
- Не выдумывать облачные зависимости в прод-пути.
- Не выдумывай новые зависимости, методы, классы и тому подобное, если где-то происходит конфликт, то необходимо прервать написание и обратиться с вопросом.
- Любое изменение dim/токенизатора = bump версии `model_card.json` + миграция Room.
- APK v1 всегда собирается и работает в авиарежиме.
- При создании временных файлов, они обязательно позже должны быть удалены.
- Любой написанный код должен быть протестирован через написанные тесты
- Запрещено читать секреты, это возможно только с использованием кода, который будет заменять сами секреты на спецсимвол '*', например "DB_PORT=****".

## 11. Обязательная проверка ошибок через JetBrains MCP (не пропускать)
- JetBrains MCP подключен как `remote http://127.0.0.1:64462/stream` без npx/proxy (по решению автора: порт считается стабильным, JS-рантайм не тянем). Если коннект `404/timeout` — попросить пользователя сверить порт в IDE `Settings | Tools | MCP Server`.
- После любого редактирования в `app/` (Kotlin, Android Studio/IDEA) или `ml/` (Python, PyCharm):
  1. Вызвать `jetbrains_lint_files` (для 1-3 файлов) или `jetbrains_get_file_problems` для точечной проверки.
  2. После сборки — `jetbrains_build_project`, разобрать все `errors`, не только первый.
  3. Не отмечать задачу `completed` пока есть ошибки уровня `error`. `warning` допустимы, но перечислить их в ответе.
- Skills проекта (`skill` tool): `phos-ml-export` — только для экспорта CLIP/SigLIP в ONNX; `phos-offline-check` — только для проверки офлайн-сборки Android. Plugins не используем в v1 (решение автора: без JS/TS).
- Сторонние скиллы из `github.com/mattpocock/skills` (MIT), установлены вручную в `.opencode/skills/` без Node/npx: `tdd` (red-green-refactor под п. §10 про тесты), `grilling` (интервью по дизайну до кода), `writing-for-agents` (написание доков/скиллов), `setup-matt-pocock-skills` (разовая настройка репо, правит этот файл и `docs/agents/`).

## 12. Agent skills

### Issue tracker

Тикеты — локальные markdown-файлы в `.scratch/<feature>/` этого репо (без внешних CLI). See `docs/agents/issue-tracker.md`.

### Domain docs

Single-context: `GLOSSARY.md` + `docs/adr/` в корне. See `docs/agents/domain.md`.
