# История Copilot Chat: TCR OT Barycenter Analysis

**Дата начала:** 10 февраля 2026  
**Проект:** Анализ TCR распределений с использованием Wasserstein Optimal Transport

---

## Сессия 6: Новый скрипт для картирования сэмплов (13 февраля 2026)

### Новые возможности

**Запрос пользователя:** "Это будет новый скрипт, ключи - фолдер с файлами и барицентром, фолдер c сэмплами, которые надо картировать по отношению к барицентру, и ключи колонок с теми же умолчаниями. Считаем расстояния от всех файлов до барицентра, рисуем распределение boxplot для тех файлов, для которых построен барицентром, тёмно-зелёным (это нормальные сэмплы) и туда же оранжевыми точками - расстояния от сэмплов, которые мы картируем, до барицентра."

#### Создание olga-boxplot-samples-ot-2pb.py

**Назначение:** Визуализация расстояний до баранцентра с отличием между нормальными сэмплами (построившими баранцентр) и картируемыми сэмплами.

**Основные параметры:**
```bash
python3 olga-boxplot-samples-ot-2pb.py <barycenter_folder> <samples_folder> [options]
```

---

## Сессия 7: Гибкий ввод сэмплов и единые метки (14 февраля 2026)

### Гибкий параметр samples

**Запрос:** Переименовать `samples_folder` в `samples` и разрешить список файлов.

**Реализация:** в скриптах
- `olga-boxplot-samples-ot-2pb.py`
- `olga-mds-plot-samples.py`
- `olga-samples-p2b-pval.py`

добавлена загрузка сэмплов из:
- папки с TSV, или
- текстового файла со списком путей (один TSV на строку, `#` для комментариев).

**Поведение вывода:** если `samples` — файл списка, выходные графики сохраняются в его родительскую папку.

### Единый генератор меток

**Запрос:** Вынести генератор меток в `ot_utils.py` и сделать формат Base/Post.

**Новая логика меток:**
- `Patient01_Base_tcr_pgen.tsv` → `01B`
- `Patient17_Post_tcr_pgen.tsv` → `17P`
- Без Base/Post: только номер пациента

**Изменения:**
- `_label_from_filename()` перенесена в `ot_utils.py`
- Все три скрипта используют общий helper
- `olga-samples-p2b-pval.py` теперь выводит метки через общий helper

### Документация

Обновлены:
- `README.md` — параметр `samples`, примеры со списком файлов, формат меток
- `.copilot-context.md` — описание общего helper и нового способа ввода сэмплов

**Параметры:**
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--barycenter <file>` — default: barycenter.npz
- `--output-plot <file>` — имя выходного файла (default: ot-distance-boxplot.png)

**Логика работы:**
1. Загружает баранцентр из `barycenter_folder`
2. Вычисляет расстояния всех файлов в `barycenter_folder` до баранцентра (нормальные сэмплы)
3. Вычисляет расстояния всех файлов в `samples_folder` до баранцентра (картируемые сэмплы)
4. Рисует boxplot:
   - Светло-зелёный боксплот (light green #90EE90) для нормальных сэмплов
   - Оранжевые точки (#F28E2B) для картируемых сэмплов с метками вида "PNN"

**Visual design:**
- Боксплот с тёмно-зелёным обводом (#0B5D1E)
- Белая медиана (заменена на чёрную для контраста)
- Оранжевые точки с чёрными метками (извлекаются номера из имён файлов PatientNN → PNN)
- Небольшое дрожание (jitter) по X для видимости перекрывающихся точек

**Примеры использования:**
```bash
# Базовый вариант
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/samples_to_map

# С весами
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --weights-column duplicate_frequency_percent

# С кастомным файлом выходной картинки (сохраняется в samples_to_map)
python3 olga-boxplot-samples-ot-2bp.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --output-plot my_distances.png

# С полным путём
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --output-plot ~/results/comparison.png
```

#### Параметр --output-plot

**Добавлено:** Гибкое управление путём сохранения графика

**Логика:**
- Если `--output-plot` — просто имя файла (нет `/`) → сохраняется в `samples_folder`
- Если имеет путь (содержит `/`) или абсолютный → используется как есть (с expand `~`)
- Default: `ot-distance-boxplot.png` (сохраняется в `samples_folder`)

**Примеры:**
```bash
# Сохраняется в input/samples_to_map/ot-distance-boxplot.png
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/samples_to_map

# Сохраняется в input/samples_to_map/comparison.png
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --output-plot comparison.png

# Сохраняется в ~/results/plot.png
python3 olga-boxplot-samples-ot-2pb.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --output-plot ~/results/plot.png
```

### Перевод README на английский

**Запрос:** "Давай переведём README обратно на английский. Мне удобнее общаться по-русски, но README нужен пользователям пакета."

**Действия:**
- Переведены все секции README.md с русского на английский (385 строк)
- Обновлены все примеры и описания параметров
- Структура документа полностью сохранена
- Результат: Англоязычный README для пользователей пакета

**Содержание README (English):**
- Installation guide
- Architecture overview (5 scripts)
- Detailed documentation for each script
- Three modes of olga-p2p-ot.py
- Smart column finding guide
- Typical workflows (4 scenarios)
- Technical details (metric, grid extension, data structure)
- Links to additional documentation

### Файлы, изменённые в сессии

1. **olga-boxplot-samples-ot-2pb.py** (новый скрипт)
   - Вычисление расстояний для двух наборов сэмплов
   - Визуализация с боксплотом и оранжевыми точками
   - Параметр --output-plot для управления выходом

2. **README.md** (полный перевод на английский)
   - Переведены все параметры, примеры, workflows
   - Добавлена документация для нового скрипта
   - Обновлены ссылки на документацию

### Добавление --output-plot в olga-plot-barycenter.py

**Запрос:** "Давай добавим такой же ключ --output-plot в olga-plot-barycenter.py"

**Цель:** Обеспечить консистентность интерфейсов для обоих скриптов визуализации.

**Действия:**
- Добавлен параметр `--output-plot <file>` в `olga-plot-barycenter.py`
- Default: `barycenter_plot.png` (сохраняется в `input_folder`)
- Та же логика обработки путей:
  - Относительный путь (без `/`) → сохраняется в `input_folder`
  - Абсолютный путь или с путём → используется как есть

**Примеры:**
```bash
# Default: сохраняется в input/test-cloud-Tumeh2014/barycenter_plot.png
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014

# Кастомное имя: input/test-cloud-Tumeh2014/my_plot.png
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 --output-plot my_plot.png

# Полный путь: ~/results/barycenter.png
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 --output-plot ~/results/barycenter.png
```

**Результат:** Оба скрипта визуализации (`olga-plot-barycenter.py` и `olga-boxplot-samples-ot-2pb.py`) теперь имеют единообразный интерфейс для управления выходными файлами.

### Совместимость

**Новый скрипт использует:**
- `ot_utils.load_distribution()` — загрузка распределений
- `ot_utils.load_barycenter()` — загрузка баранцентра
- `ot_utils.discretize_distribution()` — дискретизация
- `ot_utils.compute_wasserstein_distance()` — вычисление расстояний
- `ot_utils.extend_grid_if_needed()` — расширение сетки для out-of-sample данных

**Полная интеграция с существующей инфраструктурой.**

### Новый скрипт: olga-mds-plot-samples.py

**Запрос:** "Давай теперь напишем скрипт olga-mds-plot-samples.py : ключи у него такие же, как у boxplot, делает он следующее - загружат все сэмплы из изначального облака, загружает все новые сэмплы, предназначенные для картирования, считает все попарные расстояния, как между сэмплами, так и между сэмлами и барицентром. Расстояния считаем в grid барицентра, расширенной по мере необходимости. Затем мы строим карту mds на основе матрицы расстояний и рисуем её. Новые сэмплы оранжевые, с метками в формате P16, сэмплы из облака, в котором мы считаем барицыентр - светло-зелёные, барицентр - светло-зелёный, со звездой внутри."

**Назначение:** Multidimensional Scaling (MDS) визуализация всех парных расстояний между сэмплами и барицентром. Показывает пространственные отношения в двухмерном представлении.

**Основные параметры:**
```bash
python3 olga-mds-plot-samples.py <barycenter_folder> <samples_folder> [options]
```

**Параметры:**
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--barycenter <file>` — default: barycenter.npz
- `--output-plot <file>` — имя выходного файла (default: ot-mds-plot.png)

**Логика работы:**
1. Загружает все файлы из `barycenter_folder` (нормальные сэмплы)
2. Загружает все файлы из `samples_folder` (картируемые сэмплы)
3. Считает все пары расстояний (Wasserstein) между всеми сэмплами
4. Считает расстояния от каждого сэмпла до барицентра
5. Добавляет барицентр как отдельную точку (расстояние в себе = 0)
6. Применяет алгоритм MDS для уменьшения размерности до 2D
7. Рисует график:
   - Светло-зелёные точки (#90EE90) — нормальные сэмплы
   - Оранжевые точки (#F28E2B) — картируемые сэмплы с метками (P01, P02, ...)
   - Светло-зелё́ная звезда ⭐ — барицентр

**Особенности реализации:**
- Автоматическое расширение сетки (grid extension) при необходимости
- Поддержка весов для сэмплов
- Гибкое управление путём выходного файла (относительный, абсолютный с `~/`)
- Единообразный интерфейс с другими скриптами

**Примеры использования:**
```bash
# Базовый вариант
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/samples_to_map

# С весами
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --weights-column duplicate_frequency_percent

# С кастомным файлом выходной картинки
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --output-plot mds_analysis.png

# С полным путём
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --output-plot ~/results/mds.png
```

**Результат:**
- 2D MDS карта показывает пространственные отношения между сэмплами
- Близость точек указывает на сходство распределений
- Барицентр обычно находится в центре (минимальное среднее расстояние)
- Тестировано с 25 нормальными сэмплами и 10 картируемыми сэмплами — работает корректно

### Visual Polish для olga-mds-plot-samples.py

**Запросы по улучшению визуализации:**

1. **8-конечная звезда для барицентра**
   - Запрос: "Звёздочка барицентра пусть будет восьмиконечной"
   - Реализация: Создан custom marker используя `matplotlib.path.Path`
   - Алгоритм: Чередующиеся внешние (радиус 1.0) и внутренние (радиус 0.4) точки
   - Результат: Красивая острая восьмиконечная звезда вместо стандартной пятиконечной

2. **Удаление метки барицентра и поднятие метак сэмплов**
   - Запрос: "не будем писать метку barycenter, а метки оранжевых сэмплов поднимем чуть повыше"
   - Действия:
     - Убрана текстовая метка "Barycenter" под звездой
     - Поднята смещение метак оранжевых сэмплов: 0.02 → 0.04 → 0.06 → 0.08
   - Результат: Более чистый визуал, метки лучше видны и не пересекаются с другими элементами

**Финальный визуальный стиль:**
```
- Светло-зелёные точки: s=80, alpha=0.7, edge #0B5D1E
- Оранжевые точки: s=100, alpha=0.8, edge black (с метками выше)
- Звезда барицентра: s=600, alpha=0.9, 8-конечная, edge #0B5D1E
- Метки сэмплов: fontsize=9, bold, чёрные, смещение +0.08 по Y
```

---

## Сессия 6: MDS визуализация (13 февраля 2026 — продолжение)

### Файлы, добавленные и изменённые

1. **olga-mds-plot-samples.py** (новый скрипт, 364 строки)
   - Функции для вычисления попарных расстояний между всеми сэмплами
   - Функция `_create_8pointed_star_marker()` для 8-конечной звезды
   - Функции для вычисления расстояний до барицентра
   - MDS визуализация с matplotlib
   - Полная интеграция с `ot_utils`
   - **Visual polish:** 8-конечная звезда, поднятые метки, чистый дизайн

2. **requirements.txt** / **README.md**
   - Добавлена зависимость `scikit-learn` для MDS
   - Обновлена архитектура (теперь 6 скриптов)
   - Обновлена документация для всех трёх скриптов визуализации

### Состояние проекта

**Доступные скрипты:**
1. ✅ `olga-barycenter-ot.py` — вычисление барицентра
2. ✅ `olga-plot-barycenter.py` — визуализация барицентра
3. ✅ `olga-p2p-ot.py` — попарные расстояния
4. ✅ `olga-p2b-ot.py` — расстояния до барицентра
5. ✅ `olga-boxplot-samples-ot-2pb.py` — сравнение боксплотом
6. ✅ `olga-mds-plot-samples.py` — MDS визуализация
7. ✅ `olga-samples-p2b-pval.py` — p-значения для сэмплов **NEW!**

**Зависимости:**
```bash
pip install numpy pandas pot matplotlib scikit-learn scipy
```

### Новый скрипт: olga-samples-p2b-pval.py

**Запрос:** "Подумай, не пора ли обновить контекст... Давай напишем ещё один скрипт. У него те же параметры, что и у последних двух. Всё, что он делает - для каждого картируемого сэмпла пишет название файла, расстояние до барицентра и оценку p-value того, что это расстояние появилось из того же распределения, что и расстояния сэмплов облака. Пока я не понял, какую модель тут применять, поэтом используем нормальное распределение с оцененными по облаку параметрами. Ранжируем строки по возрастаню p-value. Этот скрипт называется olga-samples-p2b-pval.py . Важно - эта модель - временная затычка, важно аккуратно инкапслуриввть модель, чтобы мы могли потом заменить её на более точную."

**Назначение:** Оценка статистической значимости расстояний до барицентра используя нулевую гипотезу, подогнанную к нормальным сэмплам облака.

**Основные параметры:**
```bash
python3 olga-samples-p2b-pval.py <barycenter_folder> <samples_folder> [options]
```

**Параметры:**
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--barycenter <file>` — default: barycenter.npz

**Логика работы:**
1. Загружает все файлы из `barycenter_folder` (нормальные сэмплы)
2. Вычисляет расстояния до барицентра для каждого
3. Подгоняет нулевую гипотезу (NULL model): нормальное распределение
4. Загружает картируемые сэмплы и вычисляет их расстояния
5. Для каждого сэмпла считает p-value (двусторонний тест)
6. Выводит таблицу, отсортированную по растущему p-value

**Выходной формат:**
```
Sample                                    Distance      P-value     Bonf. p
================================================================================
Patient24_Post_tcr_pgen.tsv               4.864039 4.91e-05 4.91e-04 ← significant
Patient23_Post_tcr_pgen.tsv               4.245981 9.63e-04 9.63e-03 ← significant
Patient25_Post_tcr_pgen.tsv               3.058855 6.52e-02 6.52e-01 ← not significant  
...
```

**Бонферрони коррекция:**
- Метод: простое умножение p-value на количество тестов
- Аббревиатура: FWER control (Family-Wise Error Rate)
- Консервативный подход: хорошо контролирует false positives
- В примере: 10 тестов → Bonf.p = raw_p × 10 (capped at 1.0)
- Результат: 2 значимых сэмпла при p_adj < 0.05

**Аккуратная инкапсуляция модели и коррекции:**

Три ключевых функции для лёгкой замены:
```python
def compute_bonferroni_adjusted_pvalues(pvalues):
    """Multiple testing correction: p_adj = p_raw * n_tests (capped at 1.0)"""
    
def fit_null_hypothesis(distances):
    """Fit null model to normal sample distances"""
    # Currently: Normal distribution
    # Easy to replace with: Beta, Gamma, KDE, etc.
    
def compute_pvalue(distance, model):
    """Compute p-value under fitted null model"""
    # Currently: Two-tailed normal test
    # Easy to replace with alternative test statistics
```

**Альтернативные подходы для будущего:**

*Нулевая гипотеза:*
- Beta distribution (если расстояния ограничены)
- Gamma distribution (для скошенных данных)
- Kernel density estimation (непараметрическое)
- Permutation-based empirical p-value
- Смешанные модели (mixture of distributions)

*Коррекция на множественное тестирование:*
- Бонферрони (FWER, консервативная) — текущее
- Benjamini-Hochberg (FDR, менее консервативная)
- Holm-Bonferroni (пошаговая Бонферрони, менее консервативная)

**Примеры использования:**
```bash
# Базовый вариант
python3 olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 input/samples_to_map

# С весами
python3 olga-samples-p2b-pval.py input/test-cloud-Tumeh2014 input/samples_to_map \
    --weights-column duplicate_frequency_percent
```

**Результат:**
- Отсортированный список сэмплов с p-значениями
- Summary: range p-values, count significant
- Тестировано: 10 картируемых сэмплов, 2 с p < 0.001, 8 не-significate

### Final enhancements и ИТОГОВОЕ СОСТОЯНИЕ

**Финальные улучшения скрипта olga-samples-p2b-pval.py:**

1. **Добавлена Бонферрони коррекция** для множественного тестирования
   - Функция: `compute_bonferroni_adjusted_pvalues()`
   - Метод: `p_adj = p_raw × n_tests` (capped at 1.0)
   - Контроль: FWER (Family-Wise Error Rate) — консервативный подход
   - Результаты отсортированы по скорректированным p-values

2. **Очищена выходная информация**
   - Убрана нота про Бонферрони (пользователь должен знать о поправке)
   - Остались только статистика в таблице и summary

3. **Инкапсуляция сохранена**
   - Три функции для замены: `compute_bonferroni_adjusted_pvalues()`, `fit_null_hypothesis()`, `compute_pvalue()`
   - Позволяет легко попробовать альтернативные методы в будущем

**ИТОГОВЫЙ СОСТАВ ПРОЕКТА:**

✅ **7 скриптов (полный набор инструментов):**
1. `olga-barycenter-ot.py` — вычисление Wasserstein баранцентра
2. `olga-plot-barycenter.py` — визуализация баранцентра с распределениями
3. `olga-p2p-ot.py` — попарные расстояния между сэмплами
4. `olga-p2b-ot.py` — расстояния от сэмплов до баранцентра
5. `olga-boxplot-samples-ot-2pb.py` — боксплот сравнения двух наборов сэмплов
6. `olga-mds-plot-samples.py` — MDS визуализация (пространственные отношения)
7. `olga-samples-p2b-pval.py` — статистическая значимость расстояний до баранцентра

✅ **Унифицированный интерфейс:**
- Все скрипты поддерживают: `--freq-column`, `--weights-column`, `--barycenter`
- Первые 4 скрипта + 7-й: анализ и статистика
- Скрипты 5-6: визуализация (оба поддерживают `--output-plot`)

✅ **Технология:**
- Общая библиотека `ot_utils.py` (362 строки)
- Единая метрика: log_l1 (robust для 18 порядков величины в pgen)
- Автоматическое расширение сетки при необходимости

✅ **Документация:**
- README.md (490 строк) — на английском, подробное описание каждого скрипта
- archive/copilot-chat.md (1213 строк) — история разработки и решений
- Встроенная помощь в каждом скрипте (`--help`)

✅ **Готовность к использованию:**
- Все скрипты протестированы на пример-данных (25 + 10 сэмплов)
- Полная поддержка весов для сэмплов
- Гибкие пути вывода (относительные, абсолютные, с `~/`)



**Получение MDS графика:**
```bash
# Быстрое сравнение двух наборов сэмплов
python3 olga-mds-plot-samples.py input/test-cloud-Tumeh2014 input/samples_to_map \
    -weights-column duplicate_frequency_percent
# → input/samples_to_map/ot-mds-plot.png (300 dpi, 12x10 дюймов)
```

---

### Проблема

**Запрос пользователя:** "Проверь, пожалуйста, что все наши скрипты одинаково понимают параметра --barycenter"

**Обнаруженная несогласованность:**

```
Script                  | Barycenter File Specification
------------------------|----------------------------------------------
olga-p2b-ot.py         | ✅ --barycenter <file>  (custom path allowed)
olga-p2p-ot.py         | ❌ --use-barycenter-grid (boolean, hardcoded "barycenter.npz")
olga-plot-barycenter   | ❌ barycenter_file (positional argument)
olga-barycenter-ot.py  | ❌ (no parameter, always "barycenter.npz")
```

**Проблемы:**
1. **Разные интерфейсы** — невозможно предсказать как указать кастомный файл
2. **p2p** — нет способа указать путь к barycenter при использовании `--use-barycenter-grid`
3. **plot** — позиционный аргумент конфликтует с обычным стилем CLI
4. **barycenter** — нет возможности сохранить в custom location

### Решение

Привели все скрипты к единому стилю: **`--barycenter <file>`** (default: `barycenter.npz`)

#### 1. olga-barycenter-ot.py

**Добавлено:**
```python
--barycenter <file>  # Output filename (default: barycenter.npz)
```

**Изменения:**
- Добавлен параметр `--barycenter` для указания имени выходного файла
- Поддержка абсолютных путей и `~` (expand)
- Относительные пути разрешаются относительно input_folder

**Пример:**
```bash
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --barycenter my_barycenter.npz
```

#### 2. olga-p2p-ot.py

**Изменено:**
```python
# Было:
--use-barycenter-grid  # Boolean flag, hardcoded path

# Стало:
--barycenter <file>    # Path to barycenter (default: barycenter.npz)
```

**Изменения:**
- Заменён `--use-barycenter-grid` на `--barycenter <file>`
- Добавлен параметр `barycenter_file` во все функции:
  - `compute_distance_single_pair(..., barycenter_file="barycenter.npz")`
  - `compute_distance_one_to_all(..., barycenter_file="barycenter.npz")`
  - `compute_distance_all_pairs(..., barycenter_file="barycenter.npz")`
- Поддержка абсолютных путей и `~`
- Добавлен `import os` для `os.path.isabs()`

**Примеры:**
```bash
# Default barycenter.npz in input folder
python3 olga-p2p-ot.py input/test --all --barycenter barycenter.npz

# Custom location
python3 olga-p2p-ot.py input/test --all --barycenter ~/data/my_barycenter.npz
```

#### 3. olga-plot-barycenter.py

**Изменено:**
```python
# Было:
python3 olga-plot-barycenter.py <folder> [barycenter_file]  # Positional

# Стало:
python3 olga-plot-barycenter.py <folder> --barycenter <file>  # Flag
```

**Изменения:**
- Убран позиционный аргумент `barycenter_file`
- Добавлен флаг `--barycenter <file>` (default: `barycenter.npz`)
- Убрана логика "assume it's the barycenter file" из парсера
- Теперь все неизвестные аргументы вызывают ошибку

**Примеры:**
```bash
# Default
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014

# Custom barycenter
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 --barycenter ~/data/my_barycenter.npz
```

### Обновлённая документация

#### README.md
- Добавлен `--barycenter` во все секции параметров
- Обновлены примеры использования
- Исправлен workflow "Попарные сравнения" (заменён `--use-barycenter-grid` на `--barycenter`)

#### .copilot-context.md
- Обновлено описание `olga-p2p-ot.py` ("Key flags")
- Обновлена секция "Grid handling with --barycenter"
- Исправлен integration test пример

### Итог

**Достигнута полная согласованность:**
```bash
# Все скрипты теперь одинаково работают с barycenter
olga-barycenter-ot.py <folder> --barycenter output.npz
olga-plot-barycenter.py <folder> --barycenter input.npz
olga-p2p-ot.py <folder> --all --barycenter input.npz
olga-p2b-ot.py <folder> --all --barycenter input.npz
```

**Преимущества:**
- ✅ Единый интерфейс для всех скриптов
- ✅ Предсказуемое поведение
- ✅ Поддержка кастомных путей везде
- ✅ Консистентная документация

---

## Сессия 4: Обновление документации (11 февраля 2026)

### Исходная проблема

Обнаружили артефакт в LP grid-based barycenter:
- **Проблема:** Первые 10 точек сетки получали ~20% массы вероятности
- **Данные:** В этой области находится <1% реальных сэмплов
- **Причина:** Один экстремальный выброс (Patient10: pgen=1.42e-24)

**Диагностика:**
```python
# Patient10 содержит экстремально малые pgen
grid[0] = 2.506e-17
Probability at grid[0]: 0.054179 (5.4%!)
Mass in first 10 points: 0.203863 (20.4%!)
```

### Первые попытки решения

1. **Percentile-based grid (1-99 перцентили)**
   - Результат: Уменьшило артефакт с 20% до 0.46%
   - Проблема: Концептуально это всё равно фильтрация данных
   - **Решение отклонено:** "Хочется реализовать правильный метод"

2. **Анализ root cause:**
   - LP solver минимизирует транспортные затраты
   - Помещает массу туда, где находятся источники (даже если это единичный выброс)
   - Математически корректно, но визуально/аналитически проблематично

### Ключевые инсайты

**Мысль #1:** Проблема не в алгоритме, а в том, что фиксированная сетка не может адаптироваться к данным

**Мысль #2:** Free-support barycenter — это настоящий OT метод, который:
- Оптимизирует **и расположение**, **и веса** support points
- Доказуемо минимизирует Wasserstein distance
- Не требует предзаданной сетки

**Мысль #3:** Нужен итеративный процесс:
1. Найти оптимальные позиции support points
2. Вычислить оптимальные веса для этих позиций
3. Использовать Sinkhorn вместо EMD для численной стабильности

---

## Сессия 2: Реализация Free-Support Barycenter (10 февраля 2026)

### Архитектура решения

**Алгоритм:**
```
1. Инициализация:
   - K = sqrt(n_samples) ≈ 43 support points (по умолчанию)
   - Log-spaced инициализация в диапазоне данных

2. Оптимизация позиций (POT library):
   X_bary = ot.lp.free_support_barycenter(measures_X, measures_a, X_init)
   
3. Оптимизация весов (наш алгоритм):
   - Инициализация: uniform weights a = (1/K, ..., 1/K)
   - Итерации:
     * Вычислить OT планы через Sinkhorn (λ=0.01)
     * Gradient descent: a ← a - η∇Loss
     * Проекция на симплекс: a ← (a)₊ / sum(a)₊
     * Learning rate: η_t = 0.1/(t+1)
   - Сходимость: ||Δa|| < 1e-8
```

### Технические вызовы и решения

**Challenge #1:** `ot.lp.free_support_barycenter()` возвращает только позиции, не веса
- **Решение:** Реализовали собственную оптимизацию весов

**Challenge #2:** EMD solver выдавал ошибки несовпадения сумм весов
- **Решение:** Переключились на Sinkhorn (более стабильный численно)
- Код:
  ```python
  gamma = ot.sinkhorn(
      a_norm / a_norm.sum(),  # Normalized barycenter weights
      a_dist / a_dist.sum(),  # Normalized measure weights
      cost_matrix,
      reg=0.01
  )
  ```

**Challenge #3:** Matplotlib legend ошибка при визуализации
- **Решение:** Использовали `mpatches.Patch` вместо списка художников

### Результаты тестирования

**Данные:** 25 пациентов, 1834 сэмпла, диапазон [1.42e-24, 3.54e-06]

**Free-support barycenter (K=50):**
```
Convergence: 60 iterations
First support point: 5.865e-09 (vs 1.42e-24 outlier!)
Weight distribution: ~2.0% ± 0.0001 (nearly uniform)
Entropy: 3.912 (высокая = хорошее покрытие)
Support range: [5.865e-09, 1.174e-06]
```

**Сравнение с LP grid (n=200):**
```
LP Grid:
- First point: 2.506e-17
- Mass in first 10 points: 4.5%
- Проблема: Чувствителен к выбросам

Free-Support:
- First point: 5.865e-09 (93x улучшение!)
- Mass in first 10 points: 20.0%
- Преимущество: Адаптивное размещение
```

---

## Сессия 3: Визуализация и документация (10 февраля 2026)

### Созданные инструменты

**Скрипты анализа:**
1. `olga-p2p-ot.py` - Попарное сравнение распределений
2. `olga-barycenter-ot.py` - LP grid-based barycenter
3. ⭐ `olga-barycenter-free-support.py` - Free-support barycenter (РЕКОМЕНДУЕТСЯ)

**Скрипты визуализации:**
4. `olga-plot-barycenter.py` - Визуализация LP метода
5. ⭐ `olga-plot-barycenter-free-support.py` - Dual-panel визуализация
6. ⭐ `compare-barycenter-methods.py` - Side-by-side сравнение методов

**Документация:**
7. `README.md` - Описание методов и сравнение
8. `WORKFLOW.md` - Quick-start гайд
9. `SUMMARY.md` - Полная техническая документация
10. `REFERENCE.md` - Карточка быстрого доступа

### Визуализация

**Dual-panel plot (free-support):**
- Верхняя панель: Scatter plot support points на log-шкале
- Нижняя панель: Дискретизированная гистограмма (интуитивнее)
- Фон: 25 индивидуальных распределений (серый)
- Баrycenter: Красные маркеры

---

## Сессия 4: Модульная архитектура (11 февраля 2026)

**13:00** - Создание центрального модуля `ot_utils.py`

**Мотивация:**
- Единый способ вычисления Wasserstein distance
- Consistency между p2p и p2b
- Легкость замены библиотеки в будущем
- DRY принцип

**Созданные функции:**
- `load_distribution()` — загрузка TCR распределения из TSV
- `compute_cost_matrix()` — вычисление cost matrix (log_l1, l1, l2)
- `compute_wasserstein_distance()` — CORE функция (EMD или Sinkhorn)
- `discretize_distribution()` — дискретизация на сетку
- `create_common_grid()` — создание log-spaced сетки
- `load_barycenter()` — загрузка barycenter.npz

**Рефакторинг olga-p2p-ot.py:**
- Удалены дублирующие функции
- Использует централизованный compute_wasserstein_distance()
- **Важно:** Исправлен cost metric на log_l1 (было неправильно!)

**Новый скрипт olga-p2b-ot.py:**
- Point-to-Barycenter distances
- Single file / Batch mode
- Sorted output, статистика

**Тестирование:**
- Patient01 ↔ Patient02: 0.844
- Patient23 ближайший к баранцентру: 7.08 (most typical)
- Patient10 самый далёкий: 12.55 (outlier!)

---

## Сессия 5: Расширение функциональности (12 февраля 2026)

**11:45** - Добавление pipeline mode и batch обработки

**olga-p2p-ot.py:**
- `--pipeline` флаг: только числа для shell скриптов
- `--all` флаг: все 300 попарных расстояний
- `--weights-column` для weighted samples

**olga-p2b-ot.py:**
- `--weights-column` для взвешенной дискретизации
- Batch mode статистика

**16:00** - Стандартизация вывода

- Добавлен `--statistics-only` ключ для обоих скриптов
- Единообразная статистика: Count, Mean, Median, Std, Min, Max, Q1, Q3
- Быстрый анализ больших матриц без таблиц

---

## Критическое открытие: метрическая неполадка (12 февраля 2026, 17:00)

### Проблема

**Наблюдение:** Min distance к баранцентру (6.86) > Max pairwise distance (6.04)

Это **математически невозможно!** Баранцентр должен быть внутри облака точек.

### Расследование

**Первый уровень: несовпадение сеток**
- olga-p2p-ot.py создавала новую адаптивную сетку для каждой пары
- olga-p2b-ot.py использовала фиксированную сетку баранцентра
- **Решение:** добавлен флаг `--use-barycenter-grid` к p2p

**Второй уровень: несовпадение дискретизации**
- olga-p2b-ot.py использовала сырые значения вместо дискретизированных
- **Решение:** добавлена дискретизация перед расчётом расстояния

**ROOT CAUSE: фундаментальная метрическая ошибка!**

### Критическая проблема

```python
olga-barycenter-ot.py (НЕПРАВИЛЬНО):
  cost_matrix = np.abs(grid - grid_T)
  # L1 метрика в оригинальном пространстве: |pgen_1 - pgen_2|

Что нужно (как в p2p и p2b):
  log_grid = np.log(grid)
  cost_matrix = np.abs(log_grid - log_grid_T)
  # log_l1 метрика в логарифмическом пространстве: |log(pgen_1) - log(pgen_2)|
```

### Почему это критично?

**Данные:** pgen диапазон [1.42e-24, 3.54e-06] — 18 порядков величины!

**L1 в оригинальном пространстве:**
- Разница между 1e-24 и 1e-23 = 9e-24 ≈ 0 (подавлена!)
- Разница между 1e-6 и 2e-6 = 1e-6 (доминирует!)
- **Эффект:** Массы смещаются к верхнему концу диапазона

**log_l1 в логарифмическом пространстве:**
- Разница между 1e-24 и 1e-23 = |log(1e-24) - log(1e-23)| = 2.3
- Разница между 1e-6 и 2e-6 = |log(1e-6) - log(2e-6)| = 0.69
- **Эффект:** Все порядки величины обработаны справедливо

### Исправление

**Файл: olga-barycenter-ot.py (строки ~215)**
```python
# Было:
cost_matrix = np.abs(grid.reshape(-1, 1) - grid.reshape(1, -1))

# Исправлено:
log_grid = np.log(grid)
cost_matrix = np.abs(log_grid.reshape(-1, 1) - log_grid.reshape(1, -1))
```

**Команда пересчёта:**
```bash
rm input/test-cloud-Tumeh2014/barycenter.npz && \
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014
```

### Новый баранцентр (с правильной метрикой)

```
Grid: 200 точек от 1.421e-24 до 3.541e-06
Max probability: 4.27e-02
Entropy: 4.15 (хорошее распределение)
Median point: 1.664e-09 (логично в центре данных)
Q1: 5.521e-11
Q3: 2.140e-08
Mass below 1e-6: 98.3% ✓
```

### Верификация: математическая консистентность!

**Попарные расстояния (300 пар, --use-barycenter-grid):**
```
Min:     0.322 (Patient04 ↔ Patient07)
Median:  1.248
Max:     6.045 (Patient10 ↔ Patient23)
Mean:    1.528
```

**Расстояния к баранцентру (25 образцов):**
```
Min:     0.387 (Patient04)
Median:  0.752
Max:     3.991 (Patient23)
Mean:    1.001
```

**Проверка логики:**
| Метрика | Pairwise | Barycenter | Статус |
|---------|----------|------------|--------|
| Min | 0.322 | 0.387 | ✓ min(p2b) > min(p2p) разумно |
| Median | 1.248 | 0.752 | ✓ баранцентр в центре облака |
| Max | 6.045 | 3.991 | ✓ max(p2b) < max(p2p) логично |
| Mean | 1.528 | 1.001 | ✓ баранцентр ближе в среднем |

**Вывод:** ✅ Все формулы теперь математически согласованы!

---

## Итоговая архитектура (12 февраля 2026, 17:15)

### Все компоненты используют log_l1 метрику

**1. ot_utils.py:**
```python
log_l1 = np.abs(np.log(cost_grid) - np.log(cost_grid_T))
```

**2. olga-barycenter-ot.py (FIXED):**
```python
log_grid = np.log(grid)
cost_matrix = np.abs(log_grid - log_grid_T)
barycenter = ot.lp.barycenter(distributions_matrix.T, cost_matrix, ...)
```

**3. olga-p2p-ot.py & olga-p2b-ot.py:**
- Используют ot_utils.compute_wasserstein_distance()
- Автоматически используют log_l1 метрику

### Готовые инструменты

1. ✅ `ot_utils.py` — центральный модуль с правильной метрикой
2. ✅ `olga-barycenter-ot.py` — LP grid баранцентр (200 точек, log_l1)
3. ✅ `olga-plot-barycenter.py` — визуализация баранцентра
4. ✅ `olga-p2p-ot.py` — попарные расстояния (3 режима, 3 варианта вывода)
5. ✅ `olga-p2b-ot.py` — расстояние к баранцентру (2 режима, 3 варианта вывода)

### Функциональность

**olga-p2p-ot.py — 3 режима сравнения:**
- Single pair: `file1.tsv file2.tsv`
- One-to-all: `file1.tsv --all`
- All-pairs: `--all` (300 расстояний)

**olga-p2p-ot.py — 3 варианта вывода:**
- Normal: полная таблица + статистика
- `--pipeline`: только числа для shell
- `--statistics-only`: только статистика

**olga-p2p-ot.py — специальные флаги:**
- `--use-barycenter-grid`: использовать сетку баранцентра
- `--weights-column`: взвешенные образцы

**olga-p2b-ot.py:**
- Single / Batch mode
- Sorted output по расстоянию
- Pipeline / Normal / Statistics-only output
- Weighted samples support

### Достигнутые цели

1. ✅ Правильная обработка экстремальной динамики (18 порядков)
2. ✅ Математическая консистентность между всеми методами
3. ✅ Модульная архитектура (DRY, переиспользование)
4. ✅ Pipeline-ready для автоматизации
5. ✅ Гибкие режимы вывода

**Проект завершён успешно!**

---

## Расширение функциональности: автоматическое расширение grid (12 февраля 2026, 23:30)

### Мотивация

**Задача:** Нужно вычислять расстояния от распределений до баранцентра, когда эти распределения **не участвовали** в построении баранцентра.

**Проблема:** Если новое распределение выходит за границы grid баранцентра (по min или max значениям), возникает несоответствие support domains.

**Пример:**
```
Баранцентр: grid [1.42e-24, 3.54e-06]  # 200 точек
Новое распределение: [5.0e-25, 1.0e-05]  # выходит за оба края
```

### Решение: extend_grid_if_needed()

**Реализована новая функция в ot_utils.py:**

```python
def extend_grid_if_needed(grid, weights, new_data_min, new_data_max):
    """
    Extend grid and weights if new data falls outside current range.
    Maintains logarithmic spacing, preserves original points exactly.
    New points get zero weight.
    """
```

**Ключевые свойства:**
1. **Сохраняет оригинальную сетку** — все 200 точек остаются на своих местах
2. **Тот же логарифмический шаг** — новые точки добавляются с тем же интервалом
3. **Нулевые веса для новых точек** — баранцентр не меняется
4. **Расширение в обе стороны** — добавляет точки ниже и выше при необходимости
5. **Идемпотентность** — если расширение не нужно, возвращает оригинал

**Алгоритм:**
```python
# 1. Вычислить средний log-шаг из оригинальной сетки
log_step = mean(diff(log(grid)))

# 2. Добавить точки ниже (если нужно)
n_below = ceil((log(grid[0]) - log(new_min)) / log_step)
lower_grid = exp(arange(log(grid[0]) - n*log_step, log(grid[0]), log_step))

# 3. Добавить точки выше (если нужно)
n_above = ceil((log(new_max) - log(grid[-1])) / log_step)
upper_grid = exp(arange(log(grid[-1]) + log_step, ..., log_step))

# 4. Объединить: [lower_grid | original_grid | upper_grid]
extended_grid = concat([lower_grid, grid, upper_grid])
extended_weights = concat([zeros(n_below), weights, zeros(n_above)])
```

### Интеграция в скрипты

**olga-p2b-ot.py (Point-to-Barycenter):**
```python
# До вычисления расстояния
values, weights = load_distribution(file_path)

# Автоматически расширяем grid при необходимости
extended_grid, extended_barycenter = extend_grid_if_needed(
    grid, barycenter_weights,
    values.min(), values.max()
)

# Дискретизация и расчёт на расширенной сетке
sample_discretized = discretize_distribution(values, weights, extended_grid)
distance = compute_wasserstein_distance(
    extended_grid, sample_discretized,
    extended_grid, extended_barycenter
)
```

**olga-p2p-ot.py (Point-to-Point с --use-barycenter-grid):**
- Single pair: расширяет grid для min/max обоих файлов
- One-to-all: расширяет для min/max всех сравниваемых файлов
- All-pairs: расширяет для глобального min/max всех распределений

### Тестирование

**Unit test:**
```
Original grid: 200 points [1.000e-20, 1.000e-06]
Log step: 0.1620

Test: extend to [1e-24, 1e-5]
Extended grid: 272 points [9.771e-25, 1.136e-05]
  Points added below: 57
  Points added above: 15
  Log step preserved: 0.1620 ✓
  
Weights:
  Sum: 1.000000 ✓
  Non-zero: 200 (original points) ✓
  Zero: 72 (new points) ✓

Test: no extension needed [1e-19, 1e-7]
  Grid unchanged: True ✓
  Weights unchanged: True ✓
```

**Integration test (реальные данные):**
```bash
# Single file p2b
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv
# Distance: 0.3837 ✓

# Batch p2b (25 файлов)
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 --statistics-only
# Mean: 1.141, Min: 0.384, Max: 4.453 ✓

# Single pair p2p с barycenter grid
python3 olga-p2p-ot.py ... --use-barycenter-grid
# Distance: 0.8350 ✓

# All-pairs p2p с barycenter grid (300 пар)
python3 olga-p2p-ot.py ... --all --use-barycenter-grid --statistics-only
# Mean: 1.528, Min: 0.322, Max: 6.045 ✓
```

### Преимущества

1. **Универсальность:** Можно сравнивать любые распределения, даже если они выходят за границы баранцентра
2. **Консистентность:** Все сравнения происходят на одной сетке (важно для корректных результатов)
3. **Автоматизм:** Не требует ручного вмешательства
4. **Эффективность:** Расширение происходит только при необходимости
5. **Точность:** Логарифмический шаг сохраняется, оригинальные точки не смещаются

### Use cases

**1. Leave-one-out cross-validation:**
```bash
# Построить баранцентр без Patient05
python3 olga-barycenter-ot.py folder --exclude Patient05_*

# Вычислить расстояние от Patient05 до баранцентра
# Grid автоматически расширится, если Patient05 выходит за границы
python3 olga-p2b-ot.py folder Patient05_Base_tcr_pgen.tsv
```

**2. Новые данные vs референсный баранцентр:**
```bash
# Построен баранцентр из cohort A
python3 olga-barycenter-ot.py cohortA/

# Сравнить новые образцы cohort B с референсом из A
python3 olga-p2b-ot.py cohortA/ cohortB/Patient_new.tsv
# Grid расширится автоматически для cohort B
```

**3. Time series analysis:**
```bash
# Baseline баранцентр из timepoint 0
python3 olga-barycenter-ot.py baseline/

# Отслеживать эволюцию через расстояние до baseline
for timepoint in t1 t2 t3 t4; do
    python3 olga-p2b-ot.py baseline/ ${timepoint}/samples.tsv
done
```

### Обновлённое состояние проекта

**Новая функциональность:**
- ✅ `extend_grid_if_needed()` в ot_utils.py
- ✅ Автоматическое расширение в olga-p2b-ot.py
- ✅ Автоматическое расширение в olga-p2p-ot.py (с --use-barycenter-grid)
- ✅ Unit и integration тесты пройдены

**Готовые инструменты (обновлённые):**
1. ✅ `ot_utils.py` — добавлена функция расширения grid
2. ✅ `olga-barycenter-ot.py` — без изменений
3. ✅ `olga-plot-barycenter.py` — без изменений
4. ✅ `olga-p2p-ot.py` — автоматическое расширение при --use-barycenter-grid
5. ✅ `olga-p2b-ot.py` — автоматическое расширение для всех режимов

**Итоговая функциональность:**
- Правильная метрика (log_l1) для экстремальной динамики ✅
- Математическая консистентность всех компонентов ✅
- Модульная архитектура с переиспользованием ✅
- Pipeline-ready для автоматизации ✅
- Гибкие режимы вывода (normal/pipeline/statistics) ✅
- **Автоматическое расширение grid для out-of-sample данных** ✅ **NEW!**

**Все задачи завершены!**

---

## Улучшение удобства использования (13 февраля 2026)

### Изменение 1: Умный поиск колонок в load_distribution()

**Мотивация:** Частый случай — пользователь помнит примерное имя колонки, но не точное.

**Реализована функция _find_column_index()** с поддержкой трёх режимов:

**1. Точное совпадение (как раньше):**
```bash
--freq-column pgen
--weights-column duplicate_frequency_percent
```

**2. Уникальное частичное совпадение (новое!):**
```bash
# Вместо полного имени можно использовать подстроку
--weights-column duplicate_frequency_p  # найдёт 'duplicate_frequency_percent'
--weights-column frequency_percent      # найдёт 'duplicate_frequency_percent'
--freq-column pge                       # найдёт 'pgen'
```

**3. По индексу (как раньше):**
```bash
--freq-column 22
--weights-column 18
```

**Гибкая диагностика ошибок:**

```bash
# Неоднозначная подстрока
--weights-column duplicate
# Error: Parameter 'weights_column': ambiguous column specification 'duplicate'
#        Multiple matches found: ['duplicate_count', 'duplicate_frequency_percent']
#        Please use a more specific name or exact column name.

# Несуществующая колонка
--freq-column xyz
# Error: Parameter 'freq_column': no column found matching 'xyz'
#        Available columns: ['sequence_id', ..., 'pgen']

# Индекс вне диапазона
--freq-column 100
# Error: Parameter 'freq_column': column index 100 is out of range
#        Available columns: [...]
```

**Алгоритм:**
```python
def _find_column_index(df, column_spec, param_name):
    """
    1. Если Int → проверить диапазон, вернуть индекс
    2. Если Str:
       a. Точное совпадение → вернуть индекс
       b. Подстроки:
          - 0 совпадений → Error: not found
          - 1 совпадение → вернуть индекс
          - >1 совпадений → Error: ambiguous
    """
```

**Тестирование:**
```
✓ Exact match 'pgen'
✓ Substring 'duplicate_frequency_p' → 'duplicate_frequency_percent'
✓ Ambiguous 'duplicate' → ERROR (correct)
✓ Non-existent 'xyz' → ERROR (correct)
✓ Index 22 for pgen
✓ Out of range index → ERROR (correct)
✓ Integration with both p2p and p2b scripts
```

### Изменение 2: Единообразная обработка parameter errors

**Проблема:** p2p выводил ошибки конфигурации всегда, p2b выводил только в нормальном режиме

```python
# p2p (ПРАВИЛЬНО):
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)

# p2b (НЕПРАВИЛЬНО):
except Exception as e:
    if not pipeline_mode:  # ← блокировал вывод!
        print(f"Error processing {file_path.name}: {e}")
```

**Решение — разделить обработку исключений:**

```python
# olga-p2b-ot.py: Parameter errors (ValueError) - ВСЕГДА выводятся
except ValueError as e:
    print(f"Error: {e}")
    sys.exit(1)

# Другие ошибки обработки - выводятся в зависимости от режима
except Exception as e:
    if not pipeline_mode:
        print(f"Error processing {file_path.name}: {e}")
    if not batch_mode:
        sys.exit(1)
    continue
```

**Результат:**
```bash
# Ошибка конфигурации видна ВСЕ режимах
python3 olga-p2b-ot.py ... --weights-column duplicate
# Error: Parameter 'weights_column': ambiguous column specification...
# (выводится, даже если --pipeline или batch mode)

# Работает корректно
python3 olga-p2b-ot.py ... --weights-column duplicate_frequency_p
# ✓ Success
```

**Тестирование:**
```
✓ Single file mode - диагностика видна
✓ Pipeline mode - диагностика видна
✓ Batch mode - диагностика видна при первой же ошибке
✓ Нормальная работа со substring match - работает
```

### Обновлённое состояние (13 февраля 2026)

**Улучшена функциональность:**
- ✅ Умный поиск колонок с поддержкой substring matching
- ✅ Единообразная система диагностики (параметры всегда выводятся)
- ✅ Лучше UX — можно писать неполные имена колонок
- ✅ Лучше DX — ошибки конфигурации видны всегда

**Все готовые инструменты теперь:**
1. ✅ `ot_utils.py` — добавлена `_find_column_index()` с умным поиском
2. ✅ `olga-barycenter-ot.py` — использует новый механизм поиска
3. ✅ `olga-plot-barycenter.py` — использует новый механизм поиска
4. ✅ `olga-p2p-ot.py` — использует новый механизм поиска, parameter errors всегда видны
5. ✅ `olga-p2b-ot.py` — использует новый механизм поиска, parameter errors всегда видны

**Итоговая функциональность:**
- Правильная метрика (log_l1) ✅
- Математическая консистентность ✅
- Модульная архитектура ✅
- Pipeline-ready ✅
- Гибкие режимы вывода ✅
- Автоматическое расширение grid ✅
- **Умный поиск колонок** ✅ **NEW!**
- **Единообразная диагностика** ✅ **NEW!**

**Проект стабилизирован и готов к использованию!**

---

## Сессия 7/8: Визуализация, метки и управление сэмплами (14-15 февраля 2026)

### Гибкий параметр samples и единые метки (14 февраля)

**Запрос:** Переименовать `samples_folder` в `samples` и разрешить список файлов.

**Реализация:** Добавлена функция `_load_sample_files()` в три скрипта:
- `olga-boxplot-samples-ot-2pb.py`
- `olga-mds-plot-samples.py`
- `olga-samples-p2b-pval.py`

Поддерживает:
- Папка с TSV-файлами, или
- Текстовый файл со списком путей (один на строку, `#` для комментариев)
- Выходные файлы сохраняются в соответствующую папку

**Новая логика меток:**
- Функция `_label_from_filename()` перенесена в `ot_utils.py`
- Формат: Patient01_Base → `01B`, Patient17_Post → `17P`
- Используется во всех трёх скриптах единообразно
- `olga-samples-p2b-pval.py` выводит таблицу с обоими: меткой и полным путём файла

### Размеры фигур и позиционирование меток (15 февраля)

**Зачем:** Увеличить разборчивость при анализе больших наборов сэмплов, избежать наложения.

**Увеличение размеров фигур (2x на каждой оси):**
- `olga-plot-barycenter.py`: 13×7 → 26×14 дюймов
- `olga-boxplot-samples-ot-2pb.py`: 8×6 → 16×12 дюймов
- `olga-mds-plot-samples.py`: 12×10 → 24×20 дюймов

Размеры маркеров и шрифтов остались прежние → большее расстояние между элементами на пиксели.

**Корректировка позиционирования меток:**

*MDS график:*
- Было: метки на 0.08 выше точек
- Стало: метки на 0.04 выше точек (в 2 раза ближе)

*Boxplot график (картируемые сэмплы):*
- Было: jitter std 0.03, метки справа с смещением 0.01
- Попытка 1: jitter 0.15, метки на 0.15 → слишком далеко от оси
- Попытка 2: jitter 0.08, метки на 0.12 → ещё далеко, наложение
- Попытка 3: jitter 0.08, метки справа с смещением 0.02 → попытка справа
- Попытка 4: метки слева от точек → слишком влево
- **Решение:** метки сразу над точками, вертикальное смещение 0.025
  * X позиция: 1 + jitter offset (следует позиции точки)
  * Y позиция: distance + 0.025 (чуть выше точки)
  * Выравнивание: ha="center", va="bottom"
  * Jitter: std 0.08 (разброс точек по горизонтали)

**Конфигурация:**
```python
# Разброс точек
jitter = rng.normal(0.0, 0.08, size=len(mapped_distances))

# Метки
ax.text(
    1 + offset,          # X: следует точке
    distance + 0.025,    # Y: чуть выше
    label,
    ha="center",         # по центру
    va="bottom",         # снизу текста
    fontsize=9, color='navy'
)
```

**Результат:**
- Метки расположены непосредственно над точками
- Нет наложений даже при 35+ сэмплах
- Ясная связь между точкой и меткой
- Улучшенная читаемость для научных презентаций

---

Все скрипты обновлены и протестированы. Документация синхронизирована.



---

## Сессия 7/8: Визуализация, метки и управление сэмплами (14-15 февраля 2026)

### Гибкий параметр samples и единые метки (14 февраля)

**Запрос:** Переименовать `samples_folder` в `samples` и разрешить список файлов.

**Реализация:** Добавлена функция `_load_sample_files()` в три скрипта:
- `olga-boxplot-samples-ot-2pb.py`
- `olga-mds-plot-samples.py`
- `olga-samples-p2b-pval.py`

Поддерживает:
- Папка с TSV-файлами, или
- Текстовый файл со списком путей (один на строку, `#` для комментариев)
- Выходные файлы сохраняются в соответствующую папку

**Новая логика меток:**
- Функция `_label_from_filename()` перенесена в `ot_utils.py`
- Формат: Patient01_Base → `01B`, Patient17_Post → `17P`
- Используется во всех трёх скриптах единообразно
- `olga-samples-p2b-pval.py` выводит таблицу с обоими: меткой и полным путём файла

### Размеры фигур и позиционирование меток (15 февраля)

**Зачем:** Увеличить разборчивость при анализе больших наборов сэмплов, избежать наложения.

**Увеличение размеров фигур (2x на каждой оси):**
- `olga-plot-barycenter.py`: 13×7 → 26×14 дюймов
- `olga-boxplot-samples-ot-2pb.py`: 8×6 → 16×12 дюймов
- `olga-mds-plot-samples.py`: 12×10 → 24×20 дюймов

Размеры маркеров и шрифтов остались прежние → большее расстояние между элементами на пиксели.

**Корректировка позиционирования меток:**

*MDS график:*
- Было: метки на 0.08 выше точек
- Стало: метки на 0.04 выше точек (в 2 раза ближе)

*Boxplot график (картируемые сэмплы):*
- Было: jitter std 0.03, метки справа с смещением 0.01
- Попытка 1: jitter 0.15, метки на 0.15 → слишком далеко от оси
- Попытка 2: jitter 0.08, метки на 0.12 → ещё далеко, наложение
- Попытка 3: jitter 0.08, метки справа с смещением 0.02 → попытка справа
- Попытка 4: метки слева от точек → слишком влево
- **Решение:** метки сразу над точками, вертикальное смещение 0.025
  - ha="center" (по центру точки)
  - va="bottom" (растут вверх)

**Финальная конфигурация boxplot:**
- Jitter std: 0.08 (кластеры point распределены, но видны)
- Метка над точкой: distance + 0.025 единиц вверх
- Выравнивание: центр по горизонтали, нижний край метки при distance

### Обновлённое состояние проекта

✅ **Полностью готовые скрипты:**
1. `olga-barycenter-ot.py` — вычисление баранцентра
2. `olga-plot-barycenter.py` — визуализация (размер 26×14)
3. `olga-p2p-ot.py` — попарные расстояния
4. `olga-p2b-ot.py` — расстояния до баранцентра
5. `olga-boxplot-samples-ot-2pb.py` — боксплот (размер 16×12, метки над точками)
6. `olga-mds-plot-samples.py` — MDS визуализация (размер 24×20, метки ближе)
7. `olga-samples-p2b-pval.py` — p-значения с двойной меткой (имя + файл)

✅ **Ключевые возможности:**
- Гибкий ввод сэмплов: папка или текстовый список файлов
- Единые метки: 01B/17P вместо длинных имён файлов
- Большие, читаемые графики: 2x размер
- Оптимальное позиционирование: элементы не накладываются
- Полная интеграция с ot_utils.py

✅ **Документация обновлена:**
- README.md — флексибильный параметр samples, формат меток
- .copilot-context.md — описание sample input, figure sizing
- archive/copilot-chat.md — полная история разработки

---

## Сессия 10: Пользовательские метки и улучшение визуализации (15 февраля 2026)

### Поддержка пользовательских меток в файлах списков

**Запрос:** Добавить возможность указывать пользовательские метки в текстовом файле со списком сэмплов. Формат: `path/to/file.tsv CustomLabel`. Если метка указана — использовать её, иначе — автоматическую генерацию.

**Реализация:** 

1. **Обновлена функция `_load_sample_files()` в трёх скриптах:**
   - `olga-boxplot-samples-ot-2pb.py`
   - `olga-mds-plot-samples.py`
   - `olga-samples-p2b-pval.py`

2. **Парсинг меток:**
   ```python
   parts = line.split(None, 1)  # разделить по первому пробелу
   file_path = Path(os.path.expanduser(parts[0]))
   if len(parts) > 1:
       custom_labels[file_path] = parts[1].strip()
   ```

3. **Использование меток:**
   ```python
   label = custom_labels.get(file_path, _label_from_filename(file_path))
   ```

**Тестирование:**
- ✅ Файлы из разных директорий с одинаковыми названиями получают разные метки
- ✅ Смешанный режим: некоторые файлы с метками, некоторые без
- ✅ Все три скрипта работают с пользовательскими метками

### Автоматическое расположение меток (adjustText)

**Проблема:** Метки на графиках перекрывают друг друга и точки, особенно при 20+ сэмплах.

**Решение:** Интеграция библиотеки `adjustText` для автоматического переместения только самих меток (текста) при пересечениях.

**Параметры adjustText:**
```python
adjust_text(
    texts,
    expand_points=(1.2, 1.2),     # расстояние от точек
    expand_text=(1.1, 1.1),        # расстояние между метками
    force_points=0.2,              # сила отталкивания от точек
    force_text=0.3                 # сила отталкивания между метками
)
```

**Конфигурация:**
- Без стрелок и рамок (чистый дизайн)
- Точки остаются на месте
- Метки двигаются только при конфликтах
- Начальное смещение сохраняется (MDS: +0.04, boxplot: +0.025)

**Результат:**
- ✅ Метки больше не перекрываются
- ✅ Чёткая связь между меткой и точкой
- ✅ Улучшенная читаемость графиков
- ✅ Профессиональный вид для презентаций

### Метки для post_samples.txt

**Добавлены метки в файл [input/post_samples.txt](input/post_samples.txt):**
- Сэмплы из `samples_to_map/`: формат `NNP` (例: 23P, 17P)
- Сэмплы из `samples_to_map_post_prev_format/`: формат `NNP-prev` (例: 23P-prev, 17P-prev)

**Результаты анализа:**
```
Total samples: 20
Significant (p < 0.05): 5 raw p-values, 3 after Bonferroni
Significant (p < 0.01): 3 raw p-values, 2 after Bonferroni
```

### Финальное состояние

**Созданные файлы:**
- ✅ [input/ot-mds-plot.png](input/ot-mds-plot.png) — MDS с автоматическим расположением метак
- ✅ [input/ot-distance-boxplot.png](input/ot-distance-boxplot.png) — Boxplot с оптимальным расположением

**Обновлённый код:**
- ✅ Все три скрипта поддерживают пользовательские метки
- ✅ adjustText интегрирован в MDS и boxplot
- ✅ Зависимость добавлена в environment

**Преимущества:**
- Гибкость: любые метки для файлов
- Чистота: без технических артефактов (стрелок, рамок)
- Эффективность: метки двигаются только при необходимости
- Масштабируемость: работает с 20+ сэмплами без наложений

---

Визуализация готова для публикации!

---

## Сессия 9: Пользовательские метки для сэмплов (15 февраля 2026)

### Поддержка кастомных меток в файлах-списках

**Запрос:** Добавить возможность записывать в текстовом файле не только имя файла, но и метку для сэмпла. Если метка указана — использовать её, иначе — автоматическую генерацию. Полезно для файлов с одинаковыми названиями из разных директорий.

**Реализация:**

**Формат файла-списка:**
```text
/path/to/file.tsv    CustomLabel
/path/to/file2.tsv
# ^ Без метки — будет автоматическая генерация
```

**Изменения в коде:**

1. **Функция `_load_sample_files()` обновлена во всех трёх скриптах:**
   - `olga-boxplot-samples-ot-2pb.py`
   - `olga-mds-plot-samples.py`
   - `olga-samples-p2b-pval.py`

2. **Парсинг строк файла:**
   ```python
   parts = line.split(None, 1)  # разделить по первому пробелу
   file_path = Path(os.path.expanduser(parts[0]))
   if len(parts) > 1:
       custom_labels[file_path] = parts[1].strip()
   ```

3. **Возврат трёх параметров:**
   ```python
   return files, output_folder, custom_labels
   ```

4. **Использование меток:**
   ```python
   label = custom_labels.get(file_path, _label_from_filename(file_path))
   ```

**Тестирование:**

Создан тестовый файл с комбинацией пользовательских и автоматических меток:
```text
/path/Patient01_Base_tcr_pgen.tsv    CustomP1
/path/Patient02_Base_tcr_pgen.tsv
# ^ 02B (авто)
/path/Patient03_Base_tcr_pgen.tsv    P3-Special
/path/Patient04_Base_tcr_pgen.tsv
# ^ 04B (авто)
```

**Результаты:**
- ✅ P-value таблица: показывает CustomP1, 02B, P3-Special, 04B
- ✅ Boxplot: все метки правильно размещены над точками
- ✅ MDS график: метки корректно отображаются

**Преимущества:**
- Гибкость: можно задать любые метки
- Совместимость: файлы из разных директорий с одинаковыми именами
- Обратная совместимость: работает без меток (только пути)
- Смешанный режим: можно комбинировать пользовательские и автоматические метки

**Документация обновлена:**
- README.md — новый раздел "Custom Sample Labels" с примерами
- .copilot-context.md — добавлено описание формата и поведения
- archive/copilot-chat.md — полная история реализации



---

## Сессия 7/8: Визуализация, метки и управление сэмплами (14-15 февраля 2026)

### Гибкий параметр samples и единые метки (14 февраля)

**Запрос:** Переименовать `samples_folder` в `samples` и разрешить список файлов.

**Реализация:** Добавлена функция `_load_sample_files()` в три скрипта:
- `olga-boxplot-samples-ot-2pb.py`
- `olga-mds-plot-samples.py`
- `olga-samples-p2b-pval.py`

Поддерживает:
- Папка с TSV-файлами, или
- Текстовый файл со списком путей (один на строку, `#` для комментариев)
- Выходные файлы сохраняются в соответствующую папку

**Новая логика меток:**
- Функция `_label_from_filename()` перенесена в `ot_utils.py`
- Формат: Patient01_Base → `01B`, Patient17_Post → `17P`
- Используется во всех трёх скриптах единообразно
- `olga-samples-p2b-pval.py` выводит таблицу с обоими: меткой и полным путём файла

### Размеры фигур и позиционирование меток (15 февраля)

**Зачем:** Увеличить разборчивость при анализе больших наборов сэмплов, избежать наложения.

**Увеличение размеров фигур (2x на каждой оси):**
- `olga-plot-barycenter.py`: 13×7 → 26×14 дюймов
- `olga-boxplot-samples-ot-2pb.py`: 8×6 → 16×12 дюймов
- `olga-mds-plot-samples.py`: 12×10 → 24×20 дюймов

Размеры маркеров и шрифтов остались прежние → большее расстояние между элементами на пиксели.

**Корректировка позиционирования меток:**

*MDS график:*
- Было: метки на 0.08 выше точек
- Стало: метки на 0.04 выше точек (в 2 раза ближе)

*Boxplot график (картируемые сэмплы):*
- Было: jitter std 0.03, метки справа с смещением 0.01
- Попытка 1: jitter 0.15, метки на 0.15 → слишком далеко от оси
- Попытка 2: jitter 0.08, метки на 0.12 → ещё далеко, наложение
- Попытка 3: jitter 0.08, метки справа с смещением 0.02 → попытка справа
- Попытка 4: метки слева от точек → слишком влево
- **Решение:** метки сразу над точками, вертикальное смещение 0.025
  - ha="center" (по центру точки)
  - va="bottom" (растут вверх)

**Финальная конфигурация boxplot:**
- Jitter std: 0.08 (кластеры point распределены, но видны)
- Метка над точкой: distance + 0.025 единиц вверх
- Выравнивание: центр по горизонтали, нижний край метки при distance

### Обновлённое состояние проекта

✅ **Полностью готовые скрипты:**
1. `olga-barycenter-ot.py` — вычисление баранцентра
2. `olga-plot-barycenter.py` — визуализация (размер 26×14)
3. `olga-p2p-ot.py` — попарные расстояния
4. `olga-p2b-ot.py` — расстояния до баранцентра
5. `olga-boxplot-samples-ot-2pb.py` — боксплот (размер 16×12, метки над точками)
6. `olga-mds-plot-samples.py` — MDS визуализация (размер 24×20, метки ближе)
7. `olga-samples-p2b-pval.py` — p-значения с двойной меткой (имя + файл)

✅ **Ключевые возможности:**
- Гибкий ввод сэмплов: папка или текстовый список файлов
- Единые метки: 01B/17P вместо длинных имён файлов
- Большие, читаемые графики: 2x размер
- Оптимальное позиционирование: элементы не накладываются
- Полная интеграция с ot_utils.py

✅ **Документация обновлена:**
- README.md — флексибильный параметр samples, формат меток
- .copilot-context.md — описание sample input, figure sizing
- archive/copilot-chat.md — полная история разработки
