#!/usr/bin/env bash

../olga-p2b-p2b-mds-plot-samples-and-bc.py  pilot-cloud-Tumeh2014-Base/ pilot-mapped-Tumeh2014-Post/ --productive-filter
../olga-samples-p2b-pval.py  pilot-cloud-Tumeh2014-Base/ pilot-mapped-Tumeh2014-Post/ --productive-filter > pilot-productive-filter-results/post-p-values.txt
