#!/usr/bin/env bash
mkdir -p ../olga/
mkdir -p ../olga-unfiltered/

copy_by_header_word_count() {
	local filepath="$1"
	local header_words

	header_words=$(head -1 "$filepath" | wc -w | tr -d ' ')

	if [[ "$header_words" == "6" ]]; then
		cp "$filepath" ../olga/
		echo "[$header_words] copied to ../olga: $filepath"
	elif [[ "$header_words" == "23" ]]; then
		cp "$filepath" ../olga-unfiltered/
		echo "[$header_words] copied to ../olga-unfiltered: $filepath"
	else
		echo "[$header_words] skipped (no destination rule): $filepath"
	fi
}

for filepath in `find work/ -name "*tcr_pgen*" -and -name "*tsv" -and -name "Patient*" -and -type f`; do
	copy_by_header_word_count "$filepath"
done


