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
import collections
import sys
import math
import konstants
import csv


def parse_arguments(to_parse=None):
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
        ''' + '\n\t'.join('"{}"'.format(w) for w in konstants.app_methods)

    parser = argparse.ArgumentParser(
                description=description,
                formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('--recalc', action='store_true', help=recalc_msg)
    #parser.add_argument(
    #    '--mebr',  # dest='mebr' seems to make this a required argument ...
    #    action='store_true',  # ... even with action='store_true'
    #    help=('This flag is required for any combined application of '
    #          'chloropicrin and methyl bromide.'))

    choices = konstants.inland + konstants.coastal
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
    
    def read_tabular(dir, filename):
        values = []
        row_index = []
        with open(os.path.join(dir, filename), newline='') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',')
            col_index = [int(i) for i in next(csvreader)[1:]]
            for row in csvreader:
                if all(row):  # Omit empty rows at bottom of csv files
                    row_index.append(int(row.pop(0)))
                    row = [  # Replace "missing" values with NaN
                        float('NaN') if cell=='NA ' else float(cell)
                        for cell in row]
                    values.append(row)
        return values, row_index, col_index
    
    try:
        base_path = sys._MEIPASS
    except:
        base_path = os.getcwd()
    tables_dir = os.path.join(base_path, 'Tables', '112017')
    read_tabular = functools.partial(read_tabular, tables_dir)
    coastal_tbls = [read_tabular(csv) for csv in konstants.coastal_csv]
    inland_tbls = [read_tabular(csv) for csv in konstants.inland_csv]
    lookup_tbl = collections.defaultdict(dict)
    for i, v in enumerate(valid_methods):
        lookup_tbl[v]['coastal'] = coastal_tbls[i]
        lookup_tbl[v]['inland'] = inland_tbls[i]
    return lookup_tbl


def check_acreage(apps, limit, string):
    acreage = sum(a['app_block_size'] for a in apps)
    if acreage > limit:
        print('Combined {} acreage cannot exceed {} acres. '
              .format(string, limit) + konstants.assistance)
        sys.exit()


def recalculate(apps, cb_list):
    '''
    For overlapping non-TIF or untarped applications, each application block
    has the same buffer zone. It is found by using the highest application
    rate and total acreage of these blocks to look up values in the tables
    for each specified method, then selecting the highest value. For non-
    overlapping blocks, calculate each buffer zone based on the details of the
    individual applications--just as for the TIF applications (overlapping or
    otherwise--only the total acreage limitation matters for TIF applications).
    '''
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


def calculate_buffer(app, county_type, lookup):
    def closest_idx(param, indices, strings):
        '''
        Look up value in table, "round up to the nearest rate and block size,
        where applicable" (--Table caption), and verify that app rate and 
        app block size are within the ranges allowed in the table
        '''
        error_msg = (
            '{} ({} {}) exceeds maximum allowable {} ({} {}). '
            ) + konstants.assistance
                
        diffs = [diff for diff in map(lambda x: param - x, indices)]
        try:
            closest_diff = max(diff for diff in diffs if diff<=0)
        except ValueError:
            print(error_msg.format(
                    strings[0],
                    param,
                    strings[1],
                    strings[2],
                    indices[-1],
                    strings[1]))
            sys.exit()
        return diffs.index(closest_diff)        

    # Lookup correct table for combination of application method and county
    vals, rates, acreage = lookup[app['app_method']][county_type]
    app_rate = app['product_app_rate'] * app['percent_active'] / 100
    rate_strings = ['Application rate', 'lbs AI/acre', 'rate']
    closest_idx_rate = closest_idx(app_rate, rates, rate_strings)
    acre_strings = ['Application block size', 'acres', 'block size']
    closest_idx_acre = closest_idx(app['app_block_size'], acreage, 
                                   acre_strings)
    result = vals[closest_idx_rate][closest_idx_acre]
    if math.isnan(result):  # Verify that value is not NA
        print('Value unavailable for inputs. ' + konstants.assistance)
        sys.exit()
    else:  # If not NA, return results
        return result

def validate(args):
    '''
    Data processing and validation. (Note that application details can not be
    properly validated via add_argument's type argument, b/c the validation
    function assigned to type is applied to one element at a time, so it is
    difficult to distinguish an invalid application method from an invalid
    value for a numeric argument.)'''
    applications = []
    for i, values in enumerate(args.app_details):
        try:
            values[:-1] = [float(v) for v in values[0:3]]
        except ValueError:
            msg = ('One or more application details should have been numeric '
                   'but its value was not numeric. Please ensure that '
                   'the first three inputs for Application {} are valid '
                   'numbers.').format(i+1)
            raise argparse.ArgumentTypeError(msg)
        if values[2]<0 or values[2]>100:
            print('The percentage of the product that is chloropicrin must be '
                  'entered as a number between 0 and 100. Please enter a '
                  'valid percentage for Application {}.'.format(i+1))
            sys.exit()
        if values[-1] not in konstants.app_methods:
            msg = ('Please input a valid application method for Application '
                   '{}').format(i+1)
            raise argparse.ArgumentTypeError(msg)
        applications.append(dict(zip(konstants.keys, values)))
    return applications


def main(args):
    '''Main routine'''
    def split_apps(checklist):
        x = list(zip(*[(a,i+1) for i,a in enumerate(applications)
            if a['app_method'] in checklist]))
        return x if x else [[], []]

    # Validate applications and separate into lists of tif and untarped/non-tif
    applications = validate(args)

    # Check for prohibited applications
    for app in applications:
        if app['app_method'] == konstants.app_methods[0]:
            print('TIF strip shallow injection is prohibited. ' + 
                konstants.assistance)
            sys.exit()

    tif_methods = konstants.app_methods[1:5]
    antitif_methods = konstants.app_methods[5:]
    tif_apps, tif_apps_nums = split_apps(tif_methods)
    other_apps, other_apps_nums = split_apps(antitif_methods)

    # Check acreage, (re)calculate buffers, and print results
    lookup_table = read_tables(konstants.app_methods[1:])
    cty_type = 'coastal' if args.county in konstants.coastal else 'inland'
    args_cb = [cty_type, lookup_table]
    if tif_apps:
        check_acreage(tif_apps, 60, 'TIF')
        tif_buffers = [calculate_buffer(app, *args_cb) for app in tif_apps]
    else:
        tif_buffers = []
    if other_apps:
        check_acreage(other_apps, 40, 'non-TIF or untarped')
        other_buffers = [calculate_buffer(app, *args_cb) for app in other_apps]
        if args.recalc:
            other_buffers, other_apps = recalculate(other_apps, args_cb)
    else:
        other_buffers = []

    return list(zip(tif_buffers, tif_apps)), list(
        zip(other_buffers, other_apps)), tif_apps_nums, other_apps_nums


#def print_results(k, string, apps, buffers):
#    for i, app in enumerate(apps):
#        units = ['acres', 'lbs/acre', '%', '']
#        unit_dict = dict(zip(k, units))
#        print(string)
#        print('\t' + '\n\t'
#              .join('{}: {} {}'.format(k, str(v), unit_dict[k])
#                    for k, v in app.items()))
#        print('Application buffer-zone distance: {} feet\n'
#              .format(buffers[i]))

# The code below won't run on it's own because of last minute moving around of
# code snippets for printing that were in main. Not super important, and
# any print formatting should be done with the textwrap module/package in the
# future.
#if __name__ == "__main__":
#    args = parse_arguments()
#    tif, other = main(args)
#    print(tif)
#    print(other)
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
