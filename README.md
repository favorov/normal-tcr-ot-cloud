# TCR Optimal Transport Analysis

Набор инструментов для анализа TCR распределений с использованием Wasserstein Optimal Transport.

## Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install numpy pandas pot matplotlib
```

## Архитектура

**Центральный модуль:** `ot_utils.py` — общие функции для всех скриптов
- Единая метрика: log_l1 (для данных spanning 18 порядков величины)
- Автоматическое расширение grid для out-of-sample данных
- Умный поиск колонок (exact match → substring match)

**Скрипты:**
1. `olga-barycenter-ot.py` — вычисление Wasserstein баранцентра
2. `olga-plot-barycenter.py` — визуализация баранцентра
3. `olga-p2p-ot.py` — попарные расстояния между распределениями
4. `olga-p2b-ot.py` — расстояния от распределений до баранцентра

---

## olga-barycenter-ot.py

Вычисляет Wasserstein баранцентр из всех TSV файлов в папке.

### Использование

```bash
python3 olga-barycenter-ot.py <input_folder> [options]
```

### Параметры

- `--freq-column <col>` — колонка с частотами (default: pgen)
- `--weights-column <col>` — колонка с весами или 'off' (default: off)
- `--n-grid <n>` — количество точек сетки (default: 200)
- `--barycenter <file>` — имя файла для сохранения баранцентра (default: barycenter.npz)

### Примеры

```bash
# Базовый вариант
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014

# С весами
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# С кастомной сеткой
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --n-grid 500

# Сохранить в другой файл
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --barycenter my_barycenter.npz
```

**Выход:** Создаёт файл с grid и весами баранцентра (по умолчанию `input_folder/barycenter.npz`).

---

## olga-plot-barycenter.py

Создаёт визуализацию баранцентра с индивидуальными распределениями.

### Использование

```bash
python3 olga-plot-barycenter.py <input_folder> [options]
```

### Параметры

- `--barycenter <file>` — путь к баранцентру (default: barycenter.npz в input_folder)
- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--output <file>` — путь к выходному файлу (default: input_folder/barycenter_plot.png)

### Пример

```bash
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# С кастомным баранцентром
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 \
    --barycenter ~/data/my_barycenter.npz
```

**Выход:** PNG файл с графиком баранцентра и всех распределений.

---

## olga-p2p-ot.py

Вычисляет Wasserstein расстояния между распределениями.

### Три режима работы

**1. Single pair — расстояние между двумя файлами**
```bash
python3 olga-p2p-ot.py <input_folder> <file1.tsv> <file2.tsv>
```

**2. One-to-all — от одного файла ко всем остальным**
```bash
python3 olga-p2p-ot.py <input_folder> <file1.tsv> --all
```

**3. All-pairs — все попарные расстояния (верхний треугольник матрицы)**
```bash
python3 olga-p2p-ot.py <input_folder> --all
```

### Параметры

- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--n-grid <n>` — количество точек сетки (default: 200)
- `--barycenter <file>` — использовать сетку из баранцентра (default: barycenter.npz)
- `--pipeline` — вывод только чисел (для скриптов)
- `--statistics-only` — только статистика (без таблиц)

### Примеры

```bash
# Single pair
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv

# One-to-all с весами
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv --all \
    --weights-column duplicate_frequency_percent

# All-pairs с barycenter grid (для согласованности с p2b)
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    --all --barycenter barycenter.npz --statistics-only

# Pipeline mode (только числа)
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv --pipeline
```

**Выход:**
- Normal: таблица + статистика
- `--pipeline`: только числа (одно на строку)
- `--statistics-only`: Count, Mean, Median, Std, Min, Max, Q1, Q3

---

## olga-p2b-ot.py

Вычисляет Wasserstein расстояния от распределений до баранцентра.

### Использование

```bash
# Single file
python3 olga-p2b-ot.py <input_folder> <file.tsv> [options]

# Batch mode (все файлы)
python3 olga-p2b-ot.py <input_folder> [--all] [options]
```

### Параметры

- `--freq-column <col>` — default: pgen
- `--weights-column <col>` — default: off
- `--barycenter <file>` — путь к баранцентру (default: barycenter.npz)
- `--all` — обработать все TSV файлы
- `--pipeline` — вывод только чисел
- `--statistics-only` — только статистика

### Примеры

```bash
# Single file
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv

# Batch mode с весами
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent --statistics-only

# Pipeline mode
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    Patient01_Base_tcr_pgen.tsv --pipeline
```

**Выход:**
- Single file: расстояние + детальная информация
- Batch mode: таблица отсортированная по расстоянию + статистика
- `--pipeline`: только числа
- `--statistics-only`: только статистика

---

## Умный поиск колонок

Все скрипты поддерживают гибкое указание колонок:

**1. Точное имя:**
```bash
--freq-column pgen
--weights-column duplicate_frequency_percent
```

**2. Подстрока (если уникальна):**
```bash
--weights-column duplicate_frequency_p   # найдёт duplicate_frequency_percent
--weights-column frequency_percent       # найдёт duplicate_frequency_percent
--weights-column count                   # найдёт duplicate_count
```

**3. Индекс колонки:**
```bash
--freq-column 22       # 22-я колонка (pgen)
--weights-column 18    # 18-я колонка
```

**Диагностика:**
```bash
# Неоднозначная подстрока
--weights-column duplicate
# Error: ambiguous column specification 'duplicate'
#        Multiple matches: ['duplicate_count', 'duplicate_frequency_percent']

# Несуществующая колонка
--freq-column xyz
# Error: no column found matching 'xyz'
#        Available columns: [...]
```

---

## Типичные workflow

### 1. Построение баранцентра и анализ

```bash
# Шаг 1: Вычислить баранцентр
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# Шаг 2: Визуализировать
python3 olga-plot-barycenter.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent

# Шаг 3: Расстояния до баранцентра
python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
    --weights-column duplicate_frequency_percent --statistics-only
```

### 2. Попарные сравнения

```bash
# Все пары с согласованной сеткой
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 \
    --all --barycenter barycenter.npz \
    --weights-column duplicate_frequency_percent --statistics-only
```

### 3. Leave-one-out validation

```bash
# Для каждого пациента:
# 1. Построить баранцентр без него
# 2. Вычислить расстояние от него до баранцентра

for patient in Patient{01..25}_Base_tcr_pgen.tsv; do
    echo "Processing $patient"
    # Построить баранцентр без этого пациента
    python3 olga-barycenter-ot.py input/cohort --exclude $patient
    # Вычислить расстояние
    python3 olga-p2b-ot.py input/cohort $patient --pipeline
done
```

### 4. Shell scripting с pipeline mode

```bash
#!/bin/bash
# Найти пациента ближайшего к баранцентру

min_dist=999999
closest=""

for file in input/test-cloud-Tumeh2014/*.tsv; do
    dist=$(python3 olga-p2b-ot.py input/test-cloud-Tumeh2014 \
        $(basename $file) --pipeline)
    if (( $(echo "$dist < $min_dist" | bc -l) )); then
        min_dist=$dist
        closest=$(basename $file)
    fi
done

echo "Closest to barycenter: $closest (distance: $min_dist)"
```

---

## Технические детали

### Метрика

**log_l1 метрика в логарифмическом пространстве:**
```
cost(x₁, x₂) = |log(x₁) - log(x₂)|
```

**Почему log_l1, а не L1?**
- Данные pgen: [1.42e-24, 3.54e-06] (18 порядков величины!)
- L1 в оригинальном пространстве: различие между 1e-24 и 1e-23 ≈ 0 (подавлено)
- log_l1: все порядки величины обрабатываются справедливо

### Автоматическое расширение grid

Если данные выходят за границы баранцентра:
- Grid автоматически расширяется
- Сохраняется логарифмический шаг
- Оригинальные точки остаются на своих местах
- Новые точки получают нулевой вес

Это позволяет сравнивать любые распределения с баранцентром, даже если они не участвовали в его построении.

### Структура данных

**Входные TSV файлы:** 23 колонки, включая:
- `pgen` (col 22) — generation probability
- `duplicate_count` (col 17) — количество дубликатов
- `duplicate_frequency_percent` (col 18) — частота в процентах

**Выходные файлы:**
- `barycenter.npz` — NumPy архив с grid и weights
- `barycenter_plot.png` — визуализация

---

## Документация

Полная история разработки: `archive/copilot-chat.md`

## Лицензия

Research use only.

