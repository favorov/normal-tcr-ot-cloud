#!/usr/bin/env bash
mkdir -p ../samples_to_map/
#grep OLGA_PGEN .nextflow.log | grep "status: COMPLETED;" | grep _Post | cut -d " " -f 15,23 | sed "s/]//; s/_Post);//; s/(//" | awk '{print "cp "$2"/"$1"_Post_tcr_pgen.tsv ../samples_to_map/"}' | bash
find work/ -name "*pgen*" -and -name "*tsv" -and -name "Patient*" -exec cp {} ../samples_to_map/ \;


