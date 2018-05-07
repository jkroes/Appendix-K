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
import konstants


def parse_arguments(methods, choices, to_parse=None):
    description =\
    '''
    Calculate buffer zone as part of recommended permit conditions for
    chlorpicrin and chlorpicrin/1,3-D products, as outlined in Pesticide Use
    Enforcement Program Standards Compendium Volume 3, Restricted Materials and
    Permitting, Appendix K.'''

    recalc_msg =\
    '''
    Buffer zones may need to be recalculated if buffer zones for two
    or more applications overlap within 36 hours from the time earlier
    applications are complete until the start of later applications. These
    adjusted buffer zones can be calculated by running this script with this
    option enabled and by re-entering application details for only those
    applications with overlapping buffers. Buffer zones for applications that
    do not overlap do not need to be recalculated, and details for those
    applications should not be re-entered when calling this script with this
    option enabled.
    '''

    county_msg =\
    '''
    County in which the application takes place, in lowercase letters and
    surrounded by quotes.'''

    app_msg =\
    '''
    Application details. For each application, use this flag with the four
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
        ''' + '\n\t'.join('"{0}"'.format(w) for w in methods)

    parser = argparse.ArgumentParser(
                description=description,
                formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--recalc', action='store_true', help=recalc_msg)
    #parser.add_argument(
    #    '--mebr',  # dest='mebr' seems to make this a required argument ...
    #    action='store_true',  # ... even with action='store_true'
    #    help=('This flag is required for any combined application of '
    #          'chloropicrin and methyl bromide.'))

    rqrdNamed = parser.add_argument_group('required named arguments')
    rqrdNamed.add_argument('--county', choices=choices, required=True,
                           metavar='COUNTY', help=county_msg)
    rqrdNamed.add_argument('--app-details', nargs=4, action='append',
                           required=True,
                           metavar=('APP_BLOCK_SIZE',
                                    'PRODUCT_APP_RATE',
                                    'PERCENT_ACTIVE',
                                    'APP_METHOD'),
                           help=app_msg)

    return parser.parse_args(to_parse) if to_parse else parser.parse_args()


def read_tables(valid_methods):
    '''Read data tables and construct lookup for tables
    (see Appendix K, K-6)'''

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
    read_tabular = functools.partial(read_tabular, tables_dir)
    coastal_tbls = [read_tabular(csv) for csv in konstants.coastal_csv]
    inland_tbls = [read_tabular(csv) for csv in konstants.inland_csv]

    lookup_tbl = collections.defaultdict(dict)
    for i, v in enumerate(valid_methods):
        lookup_tbl[v]['coastal'] = coastal_tbls[i]
        lookup_tbl[v]['inland'] = inland_tbls[i]

    return lookup_tbl


def check_acreage(apps, limit, string, assist):
    acreage = sum(a['app_block_size'] for a in apps)
    if acreage > limit:
        print('Combined {} acreage cannot exceed 60 acres. '
              .format(string) + assist)
        sys.exit()

# For overlapping non-TIF or untarped applications, each application block
# has the same buffer zone. It is found by using the highest application
# rate and total acreage of these blocks to look up values in the tables
# for each specified method, then selecting the highest value. For non-
# overlapping blocks, calculate each buffer zone based on the details of the
# individual applications--just as for the TIF applications (overlapping or
# otherwise--only the total acreage limitation matters for TIF applications).


def recalculate(apps, cb_list):
    acreage = sum(a['app_block_size'] for a in apps)
    rates = [a['percent_active'] * a['product_app_rate'] / 100
             for a in apps]
    idx = rates.index(max(rates))
    for app in apps:
        app['app_block_size'] = acreage
        app['percent_active'] = apps[idx]['percent_active']
        app['product_app_rate'] = apps[idx]['product_app_rate']
    buffers = [calculate_buffer(app, *cb_list) for app in apps]
    idx2 = buffers.index(max(buffers))
    return [buffers[idx2]], [apps[idx2]]


def calculate_buffer(app, county_type, lookup, methods, assist):
    if app['app_method'] == methods[0]:
        print('TIF strip shallow injection is prohibited. ' + assist)
        sys.exit()

# Legacy from early work on integrating methyl bromide calculations
#    if app['app_method'] == methods[-1] and apps.mebr:
#        print('Untarped drip fumigations are prohibited for chloropicrin '
#              'fumigations in combination with methyl bromide. ' + assist)
#        sys.exit()

    # Lookup correct table for combination of application method and county
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

    # Lookup value in table and verify that application rate and block size
    # are within the ranges given by table's index and column headers
    error_msg = (
        '{} ({} {}) exceeds maximum allowable {} ({} {}). ') + assist

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

    # Verify that value is not NA and if so, return results
    if math.isnan(result):
        print('Value unavailable for inputs. ' + assist)
        sys.exit()
    else:
        return result


def print_results(k, string, apps, buffers):
    for i, app in enumerate(apps):
        units = ['acres', 'lbs/acre', '%', '']
        unit_dict = dict(zip(k, units))
        print(string)
        print('\t' + '\n\t'
              .join('{}: {} {}'.format(k, str(v), unit_dict[k])
                    for k, v in app.items()))
        print('Application buffer-zone distance: {} feet\n'
              .format(buffers[i]))


def main(args):

    lookup_table = read_tables(konstants.app_methods[1:])

    # Convert parsed options to list of application dicts
    applications = []
    for values in args.app_details:
        values[0:3] = [float(v) for v in values[0:3]]
        applications.append(dict(zip(konstants.keys, values)))

    # Separate applications into lists of tif and untarped/non-tif
    tif = konstants.app_methods[1:5]
    tif_apps = [a for a in applications if a['app_method'] in tif]
    other_apps = [a for a in applications if a['app_method'] not in tif]

    # Lookup the appropriate table for the county
    if args.county in konstants.coastal:
        cty_type = 'coastal'
    if args.county in konstants.inland:
        cty_type = 'inland'

    # Check acreage, (re)calculate buffers, and print results
    args_cb = [cty_type, lookup_table, konstants.app_methods,
               konstants.assistance]
    if tif_apps:
        check_acreage(tif_apps, 60, 'TIF', konstants.assistance)
        tif_buffers = [calculate_buffer(app, *args_cb) for app in tif_apps]
    else:
        tif_buffers = []
    if other_apps:
        check_acreage(other_apps, 40, 'non-TIF or untarped',
                      konstants.assistance)
        other_buffers = [calculate_buffer(app, *args_cb) for app in other_apps]
        if args.recalc:
            other_buffers, other_apps = recalculate(other_apps, args_cb)
    else:
        other_buffers = []

    return list(zip(tif_buffers, tif_apps)), list(zip(other_buffers, other_apps))

# The code below won't run on it's own because of last minute moving around of
# code snippets for printing that were in main. Not super important, and
# any print formatting should be done with the textwrap module/package in the
# future.
# if __name__ == "__main__":
#     args = parse_arguments(konstants.app_methods,
#                            konstants.inland + konstants.coastal)
#     tif, other = main(args)
#     print(tif)
#     print(other)
#     # display_results = functools.partial(print_results, konstants.keys)
#     # display_results('TIF application inputs:', tif_apps, tif_buffers)
#     # display_results('Non-TIF and untarped application inputs:',
#     #                 other_apps, other_buffers)
#     # if args.recalc:
#     #     print(konstants.mod_msg)
#     # else:
#     #     print(konstants.overlap_msg)

##### More info on... #####
# Defaultdicts:
## https://www.accelebrate.com/blog/using-defaultdict-python/
## https://stackoverflow.com/questions/16333296/how-do-you-create-nested-dict-in-python
