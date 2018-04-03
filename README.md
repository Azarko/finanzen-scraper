# finanzen-scraper
## About
Finanzen-scraper - scraping utility for www.finanzen.net.
Scraping url: https://www.finanzen.net/termine/wirtschaftsdaten/

Utility get data after post-request with specified date interval. Put data to sqlite3 table and to csv table (optionally).<br/>
In each run script try to create new db with specific name (`result.db` default). In this db it try to create or use existing table with name `results`.<br/>
For each found element script checks the table for the presence of this element, and if the item is not in the table - adds it.

## Requirements
* python 2.7 or 3+
* python packages listed in requirements.txt

To install additional packages use `pip install -r requirements.txt`

## Command line options
* -start_date [str] - start date of search interval (using in post-request). Format: dd.mm.yyyy
* -end_date [str] - finish date of search interval (using in post-request). Format: dd.mm.yyyy
* --db_name [str] - path to result database name. Default - reuslt.db
* -save_csv - set this flag for additional saving data to csv table.
* --csv_name [str] path to result csv table. Default - result.csv

## Sample or run
Input:<br/>
```python finanzen_scraper.py -start_date 19.03.2018 -end_date 26.03.2018 -save_csv --csv_name my_custom_name.csv```

Result:
* file `result.db` (sqlite3 database)
* file `my_custom_name.csv`
