#!/usr/bin/env bash

for patient in $(seq -w 16 25); do
  dist=$(../../olga-p2p-ot.py \
    "cloud-Tumeh2014-Base/Patient${patient}_Base_tcr_pgen.tsv" \
    "mapped-Tumeh2014-Post/Patient${patient}_Post_tcr_pgen.tsv" \
    --productive-filter \
    --pipeline)
  echo "Patient ${patient}: ${dist}"
done
