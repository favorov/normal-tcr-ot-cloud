#!/usr/bin/env bash
../../olga-p2b-ot.py  cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter > \
  productive-filter-results/distances.txt

../../olga-samples-p2b-pval.py cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter > \
  productive-filter-results/post-p-values.txt

../../olga-p2b-boxplot-samples-ot.py cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter \
  --output-plot productive-filter-results/boxplot.png

../../olga-p2b-ot-wilcoxon.py cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter \
  > productive-filter-results/wilcoxon.txt

../../olga-p2b-mds-plot-samples-and-bc.py  cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter \
  --output-plot productive-filter-results/mds.png

../../olga-p2b-mds-plot-samples-and-bc.py  cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter \
  --label-cloud-samples \
  --output-plot productive-filter-results/mds-labeled-cloud-samples.png
