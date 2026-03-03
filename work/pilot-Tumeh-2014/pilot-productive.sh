#!/usr/bin/env bash
../../olga-p2b-ot.py  cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter > \
  pilot-productive-filter-results/distances.txt
../../olga-samples-p2b-pval.py cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter > \
  pilot-productive-filter-results/post-p-values.txt
../../olga-boxplot-samples-ot-2pb.py cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter \
  --output-plot pilot-productive-filter-results/boxplot.png
../../olga-p2b-mds-plot-samples-and-bc.py  cloud-Tumeh2014-Base/ \
  mapped-Tumeh2014-Post/ --productive-filter \
  --output-plot pilot-productive-filter-results/mds.png
