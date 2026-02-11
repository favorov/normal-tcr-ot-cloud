We want to make a normal tissue TCR-B AA junction generation probability distribution cloud from Emerson dataset.

# from your project folder
python3 -m venv .venv
source .venv/bin/activate

olga-p2p-ot.py -- reads two files, calculates OT distance between distributions on a shared log-spaced grid

Usage:
python3 olga-p2p-ot.py <input_folder> <file1> <file2> [--freq-column <col>] [--weights-column <col>] [--n-grid <n>]

Parameters:
- input_folder: folder with TSV files
- file1: name of first TSV file
- file2: name of second TSV file
- --freq-column: column index (0-based) or column name for sample values (default: pgen)
- --weights-column: column index/name for weights or 'off' (default: off)
- --n-grid: number of grid points (default: 200)

Examples:
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv --freq-column pgen --weights-column duplicate_frequency_percent
python3 olga-p2p-ot.py input/test-cloud-Tumeh2014 Patient01_Base_tcr_pgen.tsv Patient02_Base_tcr_pgen.tsv --n-grid 500

olga-barycenter-ot.py -- reads all TSV files in a folder and computes the
Wasserstein barycenter on a shared log-spaced grid using linear-program OT
(more robust than Sinkhorn for sparse grids).

Usage:
python3 olga-barycenter-ot.py <input_folder> [--freq-column <col>] [--weights-column <col>] [--n-grid <n>]

Parameters:
- input_folder: folder with TSV files
- --freq-column: column index (0-based) or column name for sample values (default: pgen)
- --weights-column: column index/name for weights or 'off' (default: off)
- --n-grid: number of grid points (default: 200)

Examples:
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --freq-column pgen --weights-column duplicate_frequency_percent
python3 olga-barycenter-ot.py input/test-cloud-Tumeh2014 --n-grid 500

