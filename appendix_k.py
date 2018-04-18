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
import math
import itertools


def calculate_buffer(app, county):
    global app_methods, inland, coastal, assistance

    coastal_csv = [
        'Table1.csv', 'Table2.csv', 'Table3.csv', 'Table4.csv', 'Table5.csv',
        'Table6a.csv', 'Table7a.csv', 'Table8a.csv', 'Table9a.csv',
        'Table10a.csv', 'Table11a.csv', 'Table12.csv']
    inland_csv = [
        'Table1.csv', 'Table2.csv', 'Table3.csv', 'Table4.csv', 'Table5.csv',
        'Table6b.csv', 'Table7b.csv', 'Table8b.csv', 'Table9b.csv',
        'Table10b.csv', 'Table11b.csv', 'Table12.csv']

    # Handle input errors and prohibitions
    if app['app_method'] == app_methods[0]:
        print('TIF strip shallow injection is prohibited. ' + assistance)
        sys.exit()
#    if app['app_method'] == app_methods[-1] and apps.mebr:
#        print('Untarped drip fumigations are prohibited for chloropicrin '
#              'fumigations in combination with methyl bromide. ' + assistance)
#        sys.exit()

    # Read data tables and construct lookup for tables (see Appendix K, K-6)
    def read_tabular(dir, csv):
        df = pd.read_csv(
                os.path.join(dir, csv),
                index_col=0,
                na_values='NA ')
        df.dropna(inplace=True, how='all')
        # Leaving values as float since calculations may produce float results
        df.index = df.index.astype(int)
        df.columns = df.columns.astype(int)
        return df

    tables_dir = os.path.join(os.getcwd(), 'Tables', '112017')
    read_tables = functools.partial(read_tabular, tables_dir)
    coastal_tbls = [read_tables(csv) for csv in coastal_csv]
    inland_tbls = [read_tables(csv) for csv in inland_csv]

    lookup = collections.defaultdict(dict)
    for i, v in enumerate(app_methods[1:]):
        lookup[v]['coastal'] = coastal_tbls[i]
        lookup[v]['inland'] = inland_tbls[i]

    # Lookup the appropriate table
    if county in coastal:
        county_type = 'coastal'
    else:
        county_type = 'inland'

    tbl = lookup[app['app_method']][county_type]

    # Table captions: "Round up to the nearest rate and block size, where
    # applicable."
    app_rate = app['product_app_rate'] * app['percent_active'] / 100
    closest_rate = np.abs(app_rate - tbl.index.to_series()).idxmin()
    closest_idx_rate = np.where(tbl.index == closest_rate)[0][0]
    closest_size = (np.abs(app['app_block_size'] - tbl.columns.to_series())
                    .idxmin())
    closest_idx_size = np.where(tbl.columns == closest_size)[0][0]

    if closest_rate < app_rate:
        closest_idx_rate += 1

    if closest_size < app['app_block_size']:
        closest_idx_size += 1

    # Lookup value in table
    error_msg = (
        '{} ({} {}) exceeds maximum allowable {}\n({} {}). ') + assistance

    try:
        col = tbl.loc[tbl.index[closest_idx_rate]]
    except IndexError as e:
        print(error_msg.format(
                'Application rate',
                app_rate,
                'lbs AI/acre',
                'rate',
                closest_rate,
                'lbs AI/acre'))
        sys.exit()

    try:
        result = col[tbl.columns[closest_idx_size]]
    except IndexError as e:
        print(error_msg.format(
                'Application block size',
                app['app_block_size'],
                'acres',
                'block size',
                str(tbl.columns[-1]),
                'acres'))
        sys.exit()

    # Return results
    if math.isnan(result):
        print('Value unavailable for inputs. ' + assistance)
        sys.exit()
    else:
        return result


def print_result(string, app, buffer):
    global keys
    units = ['acres', 'lbs/acre', '%', '']
    unit_dict = dict(zip(keys, units))
    print(string)
    print('\t' + '\n\t'
          .join('{}: {} {}'.format(k, str(v), unit_dict[k])
                for k, v in app.items()))
    print('Application buffer-zone distance: {} feet\n'
          .format(buffer))


def print_results(string, apps, buffers):
    for i, app in enumerate(apps):
        print_result(string, app, buffers[i])


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
    'tif strip shallow injection',  # TIF strip shallow injection prohibited
    'tif broadcast shank injection',
    'tif bed injection',
    'tif strip deep injection',
    'tif drip',
    'non-tif broadcast shank injection',
    'non-tif bed injection',
    'non-tif strip injection',  # Doc doesn't specify shallow or deep
    'non-tif drip',
    'untarped broadcast or strip shallow injection',  # u.b. shallow?
    'untarped broadcast or strip deep injection',  # u.b. deep?
    'untarped bed injection',
    'untarped drip']  # Split into 2 arguments with fewer options?
tif = app_methods[1:5]

# Messages
assistance =\
'''
Please contact the California Department of Pesticide Regulation for
assistance.'''

description =\
'''Calculate buffer zone as part of recommended permit conditions for
chlorpicrin and chlorpicrin/1,3-D products, as outlined in Pesticide Use
Enforcement Program Standards Compendium Volume 3, Restricted Materials and
Permitting, Appendix K.'''

recalc_msg =\
'''Buffer zones may need to be recalculated if buffer zones for two
or more applications overlap within 36 hours from the time earlier applications
are complete until the start of later applications. These adjusted buffer zones
can be calculated by running this script with this option enabled and by
re-entering application details for only those applications with overlapping
buffers. Buffer zones for applications that do not overlap do not need to be
recalculated, and details for those applications should not be re-entered when
calling this script with this option enabled.
'''

app_msg =\
'''Application details. For each application, use this flag with the four
arguments below:

APP_BLOCK_SIZE: Size of the application block, given in acres.
Application block size is limited to 60 acres for applications using
totally impermeable films (TIF) and 40 acres for non-TIF and untarped
applications.

PRODUCT_APP_RATE: Broadcast-equivalent application rate for the
product, given in pounds per acre.

PERCENT_ACTIVE: Percent of chlorpicrin listed on the product label,
given as a number between 0 and 100 without a percentage sign.

APP_METHOD: Application method, chosen from the list below:
        ''' + '\n\t'.join('"{0}"'.format(w) for w in app_methods)

county_msg =\
'''County in which the application takes place, in lowercase letters
and surrounded by quotes.'''

mod_msg =\
'''NOTE: Displayed "inputs" may differ from user inputs. For overlapping non-
TIF or untarped application blocks, a single buffer zone is calculated based
on total acreage and largest application rate, using the table for whichever of
the application methods specified by the user returns the largest buffer-zone
distance. The inputs listed here are the inputs used to find this buffer-zone
distance.'''

overlap_msg =\
'''NOTE: Buffer zones may need to be recalculated if buffer zones for two
or more applications overlap within 36 hours from the time earlier applications
are complete until the start of later applications. These adjusted buffer zones
can be calculated by running this script with additional arguments. Please
type 'python appendix_k.py -h' into the Terminal and view the section for
optional arguments.
'''

# Command line-option parsing
parser = argparse.ArgumentParser(
    description=description,
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument(
        '--recalc',
        action='store_true',
        help=recalc_msg)

rqrdNamed = parser.add_argument_group('required named arguments')

rqrdNamed.add_argument(
    '--county',
    choices=inland+coastal,
    required=True,
    metavar='COUNTY',
    help=county_msg)

rqrdNamed.add_argument(
    '--app-details',
    nargs=4,
    action='append',
    required=True,
    metavar=(
        'APP_BLOCK_SIZE',
        'PRODUCT_APP_RATE',
        'PERCENT_ACTIVE',
        'APP_METHOD'),
    help=app_msg)

#parser.add_argument(
#    '--mebr',  # dest='mebr' seems to make this a required argument ...
#    action='store_true',  # ... even with action='store_true'
#    help=(
#        'This flag is required for any combined application of '
#        'chloropicrin and methyl bromide.'))

args = parser.parse_args()

# Convert application-details options into dict format
keys = ['app_block_size', 'product_app_rate', 'percent_active', 'app_method']
applications = []
for values in args.app_details:
    values[0:3] = [float(v) for v in values[0:3]]
    applications.append(dict(zip(keys, values)))

# Separate details into categories and check against acreage limitations
tif_apps = [a for a in applications if a['app_method'] in tif]
other_apps = [a for a in applications if a['app_method'] not in tif]

# For overlapping non-TIF or untarped applications, each application block
# has the same buffer zone. It is found by using the highest application
# rate and total acreage of these blocks to look up values in the tables
# for each specified method, then selecting the highest value. For non-
# overlapping blocks, calculate each buffer zone based on the details of the
# individual applications--just as for the TIF applications (overlapping or
# otherwise--only the total acreage limitation matters for TIF applications).
if tif_apps:
    acreage_tif = sum(a['app_block_size'] for a in tif_apps)
    if acreage_tif > 60:
        print('Combined TIF acreage cannot exceed 60 acres.' + assistance)
        sys.exit()
    tif_buffers = [calculate_buffer(tif, args.county) for tif in tif_apps]
else:
    tif_buffers = []
if other_apps:
    other_acreage = sum(a['app_block_size'] for a in other_apps)
    if other_acreage > 40:
        print('Combined non-TIF or untarped acreage cannot exceed 40 acres' +
              assistance)
        sys.exit()
    # Modify user inputs such that only the methods differ
    if args.recalc:
        other_rates = [a['percent_active'] * a['product_app_rate'] / 100
                       for a in other_apps]
        idx = other_rates.index(max(other_rates))
        for other in other_apps:
            other['app_block_size'] = other_acreage
            other['percent_active'] = other_apps[idx]['percent_active']
            other['product_app_rate'] = other_apps[idx]['product_app_rate']
    # Calculate possible buffer-zone distances
    other_buffers = [calculate_buffer(other, args.county)
                     for other in other_apps]
    # Find maximum buffer-zone distance, and corresponding application method
    # (as well as other inputs) for use in printing below
    if args.recalc:
        idx2 = other_buffers.index(max(other_buffers))
        other_buffers = [other_buffers[idx2]]
        other_apps = [other_apps[idx2]]
else:
    other_buffers = []

print_results('TIF application inputs:', tif_apps, tif_buffers)
print_results('Non-TIF and untarped application inputs:',
              other_apps,
              other_buffers)

if args.recalc:
    print(mod_msg)
else:
    print(overlap_msg)

##### More info on... #####
# Defaultdicts:
## https://www.accelebrate.com/blog/using-defaultdict-python/
## https://stackoverflow.com/questions/16333296/how-do-you-create-nested-dict-in-python