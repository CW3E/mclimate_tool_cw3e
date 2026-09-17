#!/bin/bash

set -euo pipefail

# --------------------------------------------------
# Configuration
# --------------------------------------------------

lag=4
server="merced"
source="realtime"
domains=("NPAC" "SEAK")

repo_dir="/data/projects/operations/GEFS_Mclimate"
container="/data/projects/operations/GEFS_Mclimate/envs/GEFS_Mclimate.sif"

ivt_dir="/data/projects/derived_products/GEFS_IVT/data"

output_base="${repo_dir}/output/images/mclimate/v1/GEFS_50"
website_base="/data/projects/website/mirror/htdocs/images/mclimate/v1/GEFS_50"

max_copy_attempts=5
copy_timeout=240
copy_retry_sleep=5

# --------------------------------------------------
# Date
# --------------------------------------------------

init_date="2026091700"

echo "Running GEFS MClimate for ${init_date}"

cd "$repo_dir"

# --------------------------------------------------
# Wait for IVT file to finish writing
# --------------------------------------------------

filename="${ivt_dir}/GEFS_IVT_${init_date}.nc"

echo "Waiting for IVT file:"
echo "  ${filename}"

while true; do

    if [[ -e "$filename" ]]; then

        filesize1=$(stat --format="%s" "$filename")
        sleep 5
        filesize2=$(stat --format="%s" "$filename")

        if [[ "$filesize1" == "$filesize2" ]]; then
            break
        else
            echo "$(date -u): File is still being written."
            sleep 30
        fi

    else
        echo "$(date -u): File does not exist yet."
        sleep 30
    fi

done

echo "$(date -u): ${filename} is ready for processing."

# --------------------------------------------------
# Cleaning old cfgrib index files
# --------------------------------------------------
echo "Cleaning old cfgrib index files..."
find "${repo_dir}/data/cfgrib_index_files" \
    -type f \
    -name "*.idx" \
    -mmin +1440 \
    -delete

# --------------------------------------------------
# Run intermediate-product processing
# --------------------------------------------------

echo
echo "STARTING PRODUCT GENERATION at $(date -u)"

singularity exec \
    --bind /data:/data \
    -e "$container" \
    /opt/conda/envs/container/bin/python \
    main.py \
    --init-date "$init_date" \
    --source "$source" \
    --server "$server"

echo "Intermediate products completed at $(date -u)"

# --------------------------------------------------
# Run plotting for each domain
# --------------------------------------------------

for domain in "${domains[@]}"; do

    echo
    echo "Creating plots for ${domain} at $(date -u)"

    singularity exec \
        --bind /data:/data \
        -e "$container" \
        /opt/conda/envs/container/bin/python \
        main_plot.py \
        --init-date "$init_date" \
        --domain "$domain" \
        --source "$source" \
        --server "$server"

    echo "Finished plotting ${domain} at $(date -u)"

done

# --------------------------------------------------
# Copy figures to website mirror
# --------------------------------------------------

echo
echo "Copying figures to website mirror at $(date -u)"

for domain in "${domains[@]}"; do

    source_dir="${output_base}/${domain}/${init_date}/1"
    destination_dir="${website_base}/${domain}/${init_date}/1"

    echo
    echo "Domain: ${domain}"
    echo "Source: ${source_dir}"
    echo "Destination: ${destination_dir}"

    if [[ ! -d "$source_dir" ]]; then
        echo "ERROR: Source directory does not exist:"
        echo "  ${source_dir}"
        exit 1
    fi

    mkdir -p "$destination_dir"

    # Check whether there are actually PNG files to copy
    shopt -s nullglob
    png_files=("${source_dir}"/*.png)
    shopt -u nullglob

    if [[ ${#png_files[@]} -eq 0 ]]; then
        echo "WARNING: No PNG files found in ${source_dir}"
        continue
    fi

    copied=false

    for ((attempt=1; attempt<=max_copy_attempts; attempt++)); do

        echo "Copy attempt ${attempt}/${max_copy_attempts} for ${domain}"

        if timeout "$copy_timeout" rsync \
            --ignore-missing-args \
            -avih \
            "${source_dir}/"*.png \
            "${destination_dir}/"; then

            echo "Successfully copied ${domain} figures."
            copied=true
            break

        else
            echo "Copy attempt ${attempt} failed."

            if (( attempt < max_copy_attempts )); then
                echo "Retrying in ${copy_retry_sleep} seconds..."
                sleep "$copy_retry_sleep"
            fi
        fi

    done

    if [[ "$copied" != true ]]; then
        echo "ERROR: Failed to copy ${domain} figures after ${max_copy_attempts} attempts."
        exit 1
    fi

done

# --------------------------------------------------
# Copy renamed files to operational image directory - DELETE THIS AFTER NEW WEBSITE HAS LAUNCHED
# --------------------------------------------------
operational_dir="/data/projects/website/mirror/htdocs/Projects/MClimate/images/images_operational"
for domain in "${domains[@]}"; do    
    for source_file in "${png_files[@]}"; do
    
        filename=$(basename "$source_file")
    
        if [[ "$filename" =~ __F([0-9]{3})\.png$ ]]; then
            F_num=$((10#${BASH_REMATCH[1]}))
        else
            echo "WARNING: Could not extract forecast lead from ${filename}"
            continue
        fi
    
        destination_filename="${domain}_mclimate_F${F_num}.png"
        destination_file="${operational_dir}/${destination_filename}"
    
        copied_operational=false
    
        for ((attempt=1; attempt<=max_copy_attempts; attempt++)); do
    
            echo "Copying ${filename} -> ${destination_filename}"
            echo "Attempt ${attempt}/${max_copy_attempts}"
    
            if timeout "$copy_timeout" cp "$source_file" "$destination_file"; then
                copied_operational=true
                break
            else
                echo "Operational copy attempt ${attempt} failed."
                if (( attempt < max_copy_attempts )); then
                    sleep "$copy_retry_sleep"
                fi
            fi
        done
    
        if [[ "$copied_operational" != true ]]; then
            echo "ERROR: Failed to copy ${filename} to:"
            echo "  ${destination_file}"
            exit 1
        fi
    
    done

echo
echo "GEFS MClimate completed successfully at $(date -u)"

# --------------------------------------------------
# Remove intermediate netCDF files
# --------------------------------------------------
echo "Cleaning intermediate NetCDF files..."
processed_dir="${repo_dir}/output/processed/${source}/${init_date}"
forecast_file="${processed_dir}/forecast.nc"
diagnostics_file="${processed_dir}/diagnostics.nc"
echo "Intermediate files removed."

rm -f "$forecast_file" "$diagnostics_file"

exit 0


