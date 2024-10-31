#! /bin/bash

# Save the current directory path in a variable
BASE_DIR=$(pwd)
cd "$BASE_DIR/paper_spider"

# Define the years to scrape
years=(2024 2023 2022 2021)

# Loop through each year and run the scrapy command
for year in "${years[@]}"; do
    output_file="$BASE_DIR/data/CVPR_${year}.json"
    
    # Check if the file already exists
    if [ -f "$output_file" ]; then
        echo "File for year $year already exists. Skipping..."
    else
        # Run scrapy if the file doesn't exist
        echo "Scraping data for year $year..."
        scrapy crawl cvf_paper_spider -O "$output_file" -a conference=CVPR -a year="$year"
    fi
done
