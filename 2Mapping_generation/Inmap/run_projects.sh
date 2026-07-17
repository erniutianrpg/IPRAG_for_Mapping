#!/bin/bash

declare -a projects=("bigbluebutton" "teammates" "teastore" "jabref" "mediastore" "hadoop")
#declare -a projects=("bigbluebutton")
for project in "${projects[@]}"; do
    base_path="dataset/${project}"
    

    module_info_file="${base_path}/Extracted_Module.txt"


    gt_file="${base_path}/groundtruth.json"
    output_dir="${project}"

    mkdir -p "$output_dir"

    echo "Running for $project project..."

    if [[ "$project" == "hadoop" ]]; then
        CUDA_VISIBLE_DEVICES=3 nohup python Main_for_hadoop.py "$base_path" -m "$module_info_file" -a tfidf -g "$gt_file" \
            > "${output_dir}/${project}.log" 2>&1 &
    else
        CUDA_VISIBLE_DEVICES=3 nohup python Main_for_tfidf.py "$base_path" -m "$module_info_file" -a tfidf -g "$gt_file" \
            > "${output_dir}/${project}.log" 2>&1 &
    fi

    sleep 120
done
