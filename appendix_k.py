# -*- coding: utf-8 -*-
"""
Author: Justin Lawrence Kroes
Agency: Department of Pesticide Regulation
Branch: Environmental Monitoring
Unit: Air Program
Date: 4/9/18
"""

import argparse
import os
import functools
import pandas as pd
import numpy as np
import collections
import sys


def read_tabular(dir, csv):
    df = pd.read_csv(
            os.path.join(dir, csv),
            index_col=0)
    df.dropna(inplace=True)
    # Leaving values as float since calculations may produce float results
    df.index = df.index.astype(int)
    df.columns = df.columns.astype(int)
    return df


# Choices for command line options
inland = [
    'alameda', 'alpine', 'amador', 'butte', 'calaveras', 'colusa',
    'contra costa', 'el dorado', 'fresno', 'glenn', 'imperial', 'inyo',
    'kern', 'kings', 'lake', 'lassen', 'madera', 'mariposa', 'merced',
    'modoc', 'mono', 'napa', 'nevada', 'placer', 'plumas', 'riverside',
    'sacramento', 'san benito', 'san bernadino', 'san joaquin',
    'santa clara', 'shasta', 'sierra', 'siskiyou', 'solano', 'stanislaus',
    'sutter', 'tehama', 'trinity', 'tulare', 'tuolumne', 'yolo', 'yuba']
coastal = [
    'del norte', 'humboldt', 'los angeles', 'marin', 'mendocino',
    'monterey', 'orange', 'san diego', 'san francisco', 'san luis obispo',
    'san mateo', 'santa barbara', 'santa cruz', 'sonoma', 'ventura']
app_methods = [
    'tif broadcast shank injection',
    'tif bed injection',
    'tif strip deep injection',  # TIF strip shallow injection prohibited
    'tif drip',
    'non-tif broadcast shank injection',
    'non-tif bed injection',
    'non-tif strip injection',  # Doc doesn't specify shallow or deep
    'non-tif drip',
    'untarped broadcast or strip shallow injection',  # u.b. shallow?
    'untarped broadcast or strip deep injection',  # u.b. deep?
    'untarped bed injection',
    'untarped drip']  # Split into 2 arguments with fewer options?

# Command line options
parser = argparse.ArgumentParser(
    description=(
        'Calculate buffer zone as part of recommended permit conditions for\n'
        'chlorpicrin and chlorpicrin/1,3-D products, as outlined in\n'
        'Pesticide Use Enforcement Program Standards Compendium Volume 3,\n'
        'Restricted Materials and Permitting, Appendix K.'),
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument(
    dest='county',
    choices=inland+coastal,
    metavar='county',
    help=(
        'County in which the application takes place.\nAccepted value:\n\t'
        'County name in lowercase letters, surrounded by quotes.'))
parser.add_argument(
    dest='app_block_size',
    type=float,
    help=(
        'Size of the application block. Application block size is limited to\n'
        '60 acres for applications using totally impermeable films (TIF) and\n'
        '40 acres for non-TIF and untarped applications.\nAccepted value:\n\t'
        'A number (in acres)'))
parser.add_argument(
    dest='product_app_rate',
    type=float,
    help=(
        'Broadcast-equivalent application rate for the product. Converted to\n'
        "application rate of chlorpicrin based on the product's percentage\n"
        'chlorpicrin.\nAccepted value:\n\tA number (in pounds per acre)'))
parser.add_argument(
    dest='percent_active',
    type=float,
    help=(
        'Percent of chlorpicrin listed on the product label.\nAccepted '
        'value:\n\t'
        'A number between 0 and 100, without a percentage sign.'))
# parser.add_argument('tarp', choices=['tif', 'non-tif', 'untarped'])
parser.add_argument(
    dest='app_method',
    choices=app_methods,
    metavar='app_method',
    # Without '+', '\n' is concatenated before the join
    help=(
        'Application method.\nAccepted values (include quotes):\n\t' +
        '\n\t'.join('"{0}"'.format(w) for w in app_methods)))
args = parser.parse_args()

# Read data tables and construct lookup for tables (see Appendix K, K-6)
tables_dir = os.path.join(os.getcwd(), 'Tables', '112017')
read_tables = functools.partial(read_tabular, tables_dir)

coastal_csv = [
    'Table1.csv', 'Table2.csv', 'Table3.csv', 'Table4.csv', 'Table5.csv',
    'Table6a.csv', 'Table7a.csv', 'Table8a.csv', 'Table9a.csv', 'Table10a.csv',
    'Table11a.csv', 'Table12.csv']
inland_csv = [
    'Table1.csv', 'Table2.csv', 'Table3.csv', 'Table4.csv', 'Table5.csv',
    'Table6b.csv', 'Table7b.csv', 'Table8b.csv', 'Table9b.csv', 'Table10b.csv',
    'Table11b.csv', 'Table12.csv']

coastal_tbls = [read_tables(csv) for csv in coastal_csv]
inland_tbls = [read_tables(csv) for csv in inland_csv]

lookup = collections.defaultdict(dict)
for i, v in enumerate(app_methods):
    lookup[v]['coastal'] = coastal_tbls[i]
    lookup[v]['inland'] = inland_tbls[i]

# Lookup the appropriate table, then buffer zone distance
if args.county in coastal:
    county_type = 'coastal'
else:
    county_type = 'inland'

tbl = lookup[args.app_method][county_type]

# Table captions: "Round up to the nearest rate and block size, where
# applicable."
app_rate = args.product_app_rate * args.percent_active / 100  # lbs AI/acre
closest_rate = np.abs(app_rate - tbl.index.to_series()).idxmin()
closest_idx_rate = np.where(tbl.index == closest_rate)[0][0]
closest_size = np.abs(args.app_block_size - tbl.columns.to_series()).idxmin()
closest_idx_size = np.where(tbl.columns == closest_size)[0][0]

if closest_rate < app_rate:
    closest_idx_rate += 1
if closest_size < args.app_block_size:
    closest_idx_size += 1

try:
    result = tbl.loc[
                tbl.index[closest_idx_rate],
                tbl.columns[closest_idx_size]]
except IndexError as e:
    print(
        'Application rate ({} lbs AI/acre) exceeds maximum allowable rate ({} '
        'lbs AI/acre). Please try again using a valid rate.'.format(
            app_rate,
            closest_rate))
    sys.exit()
except KeyError as e:
    print(
        'Application block size ({} acres) exceeds maximum acreage allowed '
        "({} acres) for the tarpaulin type of the specified application "
        'method. Please try again using a valid block size.'.format(
            args.app_block_size,
            str(tbl.columns[-1])))
    sys.exit()

print('Buffer zone distance in feet:', result)

##### More info on... #####
# Defaultdicts:
## https://www.accelebrate.com/blog/using-defaultdict-python/
## https://stackoverflow.com/questions/16333296/how-do-you-create-nested-dict-in-python

##### Tests (within Spyder) #####
#runfile('C:/Users/jkroes/Desktop/Appendix K/appendix_k.py', args='monterey 40 600 25 "untarped broadcast or strip deep injection"', wdir='C:/Users/jkroes/Desktop/Appendix K')
#runfile('C:/Users/jkroes/Desktop/Appendix K/appendix_k.py', args='monterey 40 1200 25 "untarped broadcast or strip deep injection"', wdir='C:/Users/jkroes/Desktop/Appendix K')
#runfile('C:/Users/jkroes/Desktop/Appendix K/appendix_k.py', args='monterey 40 1500 25 "untarped broadcast or strip deep injection"', wdir='C:/Users/jkroes/Desktop/Appendix K')
#runfile('C:/Users/jkroes/Desktop/Appendix K/appendix_k.py', args='monterey 300 1200 25 "untarped broadcast or strip deep injection"', wdir='C:/Users/jkroes/Desktop/Appendix K')
#runfile('C:/Users/jkroes/Desktop/Appendix K/appendix_k.py', args='monterey 300 1500 25 "untarped broadcast or strip deep injection"', wdir='C:/Users/jkroes/Desktop/Appendix K')