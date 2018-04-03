"""
    Finanzen_scraper.py - scraping utility for www.finanzen.net.
    Contain:
        - FinanzenScraper - main class with scraping and saving functions;
        - run - function with command line arguments parsing and scraper starter.
    Usage:
        python finanzen_scraper.py -start_date 19.03.2018 -end_date 26.03.2018 -save_csv --csv_name my_custom_name.csv
"""

__author__ = 'Boris Polyanskiy'

from argparse import ArgumentParser
from collections import OrderedDict
from csv import DictWriter
from os.path import isfile
from os import remove
import re
import sqlite3
from sys import stderr, version_info

from bs4 import BeautifulSoup
import requests

regex = re.compile('^\s*([\d]{2}.[\d]{2}.[\d]{4})\s*$')  # for check date format


class FinanzenScraper:
    """Class for scraping part of finanzen.net and save data to csv and db."""

    url = 'https://www.finanzen.net/termine/wirtschaftsdaten/'

    def __init__(self, start_date='', end_date=''):
        """Initialization of class.

        :param start_date: date of start parsing in format dd.mm.yyyy
        :param end_date: date of end parsing in format dd.mm.yyyy
        """
        self.start_date = start_date
        self.end_date = end_date
        self.indicator = {'teletraderBetter': 'up', 'teletraderWorse': 'down'}
        self.results = []

        # For database
        self.table_header = OrderedDict()
        self.table_header['pk'] = 'INTEGER PRIMARY KEY'
        self.table_header['time'] = 'text'
        self.table_header['country'] = 'text'
        self.table_header['relevance'] = 'integer'
        self.table_header['description'] = 'text'
        self.table_header['previous'] = 'real'
        self.table_header['forecast'] = 'real'
        self.table_header['actual'] = 'real'
        self.table_header['indicator'] = 'text'
        self.table_keys = list(self.table_header.keys())[1:]

    def scrape(self):
        """Scrape and parse web-page, store data to self.results."""
        body = {
            'stTeletraderDateBoxId': '',
            'blnTeletraderDisplayNone': 'True',
            'dtTeletraderFromDate': str(self.start_date),
            'dtTeletraderEndDate': str(self.end_date),
            'dtTeletraderFromDateMobile': '',
            'dtTeletraderEndDateMobile': ''
        }
        html = requests.post(self.url, data=body)
        bs = BeautifulSoup(html.text, 'html.parser')
        data = bs.find('div', id="ttc_1")
        for tr in data.find_all('tr'):
            cols = tr.find_all('td')
            if not cols:
                continue
            if len(cols) != 9:
                continue
            res = OrderedDict()
            res[self.table_keys[0]] = cols[0].get_text()
            res[self.table_keys[1]] = cols[2].get_text()
            res[self.table_keys[2]] = len(cols[3].find_all('span', class_="ratingStar active"))
            res[self.table_keys[3]] = cols[4].get_text()
            previous = cols[5].get_text()
            forecast = cols[6].get_text()
            actual = cols[7].get_text()
            res[self.table_keys[4]] = previous if previous else ''
            res[self.table_keys[5]] = forecast if forecast else ''
            res[self.table_keys[6]] = actual if actual else ''
            indicator = cols[8].find('div')
            indicator = indicator.attrs['class'][0] if indicator else ''
            res[self.table_keys[7]] = self.indicator.get(indicator, '')
            self.results.append(res)

    def to_csv(self, path):
        """Write parsed results to csv file.

        :param path: path to result csv file.
        :return: None
        """
        if version_info[0] == 3:
            args = dict(file=path, mode='w', encoding='utf-8', newline='')
        else:
            args = dict(name=path, mode='wb')
        with open(**args) as stream:
            writer = DictWriter(stream, self.table_keys)
            writer.writeheader()
            if version_info[0] == 3:
                writer.writerows(self.results)
            else:
                for row in self.results:
                    r = row.copy()
                    for key in r:
                        if isinstance(r[key], basestring):
                            r[key] = r[key].encode('utf-8')
                    writer.writerow(r)

    def to_sqlite(self, db_name='results.db', table_name='results', verbose=False):
        """Write results to database.

        :param db_name: path to local db.
        :param table_name: name of table in db.
        :param verbose: if True - write warnings to console.
        :return: None
        """
        conn = sqlite3.connect(db_name)
        c = conn.cursor()
        for item in self.results:
            # Try to crate table
            c.execute(
                'CREATE TABLE IF NOT EXISTS {} ({})'.format(
                    table_name,
                    ', '.join(['%s %s' % (key[0], key[1]) for key in self.table_header.items()])
                )
            )

            # Search item in table
            c.execute(
                'SELECT * FROM {} WHERE '.format(table_name) +
                ' and '.join(['%s="%s"' % (i[0], i[1]) for i in item.items()])
            )
            data = c.fetchall()
            if data:
                # Element found in table - skip it
                if verbose:
                    stderr.write('Element already in table (pk: %d). Skip it. Element: %s\n' % (data[0][0], item))
            else:
                # Add new element
                c.execute(
                    'INSERT INTO {}({}) VALUES ({})'.format(
                        table_name,
                        ', '.join([i for i in self.table_keys]),
                        ', '.join([':' + i for i in self.table_keys])
                    ),
                    item
                )
        conn.commit()
        conn.close()


def run():
    """Main function. Run FinanzenScraper and save data to db and csv (optional)"""
    parser = ArgumentParser()
    parser.add_argument('-start_date', default='', help='Date of start scraping, "dd.mm.yyyy"', type=str)
    parser.add_argument('-end_date', default='', help='Date of end scraping, "dd.mm.yyyy"', type=str)
    parser.add_argument('--db_name', default='result.db', help='Path to local db')
    parser.add_argument('-save_csv', action='store_true', help='Additional saving result in csv file')
    parser.add_argument('--csv_name', default='result.csv', help='Name of result csv file. Default: result.csv')
    args = parser.parse_args()
    if args.start_date:
        if not re.match(regex, args.start_date):
            raise ValueError('Start date must be in format dd.mm.yyyy')
    if args.end_date:
        if not re.match(regex, args.end_date):
            raise ValueError('End date must be in format dd.mm.yyyy')

    scraper = FinanzenScraper(start_date=args.start_date, end_date=args.end_date)
    scraper.scrape()
    scraper.to_sqlite(args.db_name)
    if args.save_csv:
        if isfile(args.csv_name):
            remove(args.csv_name)
        scraper.to_csv(args.csv_name)


if __name__ == '__main__':
    run()
