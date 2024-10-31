#! /bin/bash

# Save the current directory path in a variable
BASE_DIR=$(pwd)
cd "$BASE_DIR/paper_spider"

# Define the years to scrape
years=(2024 2023 2022 2021 2020 2019 2018)

# Loop through each year and run the scrapy command
for year in "${years[@]}"; do
    output_file="$BASE_DIR/data/AAAI_${year}.json"
    
    # Check if the file already exists
    if [ -f "$output_file" ]; then
        echo "File for year $year already exists. Skipping..."
    else
        # Run scrapy if the file doesn't exist
        echo "Scraping data for year $year..."
        scrapy crawl aaai_paper_spider -O "$output_file" -a year="$year"
    fi
done
