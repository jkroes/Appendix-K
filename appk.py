# -*- coding: utf-8 -*-
"""
Author: Justin Lawrence Kroes
Agency: Department of Pesticide Regulation
Branch: Environmental Monitoring
Unit: Air Program
Date: 4/9/18
"""

import os
import functools
import collections
import sys
import math
import konstants
import csv
import copy


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
    # Calculate potential buffer zones
    acreage = sum(a['block'] for a in apps)
    max_broad = max(a['broadcast'] for a in apps)
    app_copies = copy.deepcopy(apps)
    for app in app_copies:
        app['block'] = acreage
        app['broadcast'] = max_broad
    buffers = [calculate_buffer(app, *cb_list) for app in app_copies]
    buffer = max(buffers)
    idx = buffers.index(buffer)

    # Construct a single, partial application representing all apps
    # for display by the script that called this one
    new = {}
    new['number'] = ', '.join(str(a['number']) for a in apps)
    new['name'] = ', '.join(str(a['name']) for a in apps)
    new['block'] = acreage
    new['broadcast'] = max_broad
    new['method'] = apps[idx]['method']

    return [new], [buffer]


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
                    konstants.truncate(param, 1),
                    strings[1],
                    strings[2],
                    indices[-1],
                    strings[1]))
            sys.exit()

        return diffs.index(closest_diff)

    # Lookup correct table for combination of application method and county
    vals, rates, acreage = lookup[app['method']][county_type]
    rate_strings = ['Broadcast equivalent application rate', 'lbs AI/acre', 'rate']
    closest_idx_rate = closest_idx(app['broadcast'], rates, rate_strings)
    acre_strings = ['Application block size', 'acres', 'block size']
    closest_idx_acre = closest_idx(app['block'], acreage,
                                   acre_strings)
    buffer = vals[closest_idx_rate][closest_idx_acre]
    if math.isnan(buffer):  # Verify that value is not NA
        print(
            'Based on the inputs, one or more buffer zones would exceed the '
            'maximum size of half a mile. ' + konstants.assistance)
        sys.exit()
    
    return int(buffer)


def broadcast_equiv_calc(app):
    '''Convert product application rate to broadcast-
    equivalent rate, converting units if necessary.
    Note that broadcast is given in units of lbs 
    product/acre in product labels, but as lbs
    AI/acre in Appendix K's tables.
    '''
    rate_ai = app['rate'] * app['percent'] / 100
    if app['units'] == 'gal/acre':
        rate_ai *= app['density']

    broadcast = rate_ai * app['strip'] / app['center']

    return broadcast

def split_list(li, methods):
    return [el for el in li if el['method'] in methods]

def main(recalc, county, applications):
    '''Main routine'''
    for app in applications:
        # Prohibited-application check
        if app['method'] == konstants.app_methods[0]:
            print('TIF strip shallow injection is prohibited. ' +
                konstants.assistance)
            sys.exit()
        # Broadcast calculations
        app['broadcast'] = broadcast_equiv_calc(app)

    # Split applications into lists of tif and untarped/non-tif
    tif_methods, other_methods = konstants.app_methods[1:5], konstants.app_methods[5:]
    split_apps = functools.partial(split_list, applications)
    tif_apps, other_apps = map(split_apps, (tif_methods, other_methods))

    # (Re)calculate buffers, checking acreage and broadcast rates against limits
    lookup_table = read_tables(konstants.app_methods[1:])
    cty_type = 'coastal' if county in konstants.coastal else 'inland'
    args_cb = [cty_type, lookup_table]

    if tif_apps:
        tif_buffers = [calculate_buffer(app, *args_cb) for app in tif_apps]
    else:
        tif_buffers = []
    if other_apps and not recalc:
        other_buffers = [calculate_buffer(app, *args_cb) for app in other_apps]
    elif other_apps and recalc:
        other_apps, other_buffers = recalculate(other_apps, args_cb)
    else:
        other_buffers = []

    apps, buffers = tif_apps + other_apps, tif_buffers + other_buffers
    for i,app in enumerate(apps):
        app['buffer'] = buffers[i]

    return apps

##### More info on... #####
# Defaultdicts:
## https://www.accelebrate.com/blog/using-defaultdict-python/
## https://stackoverflow.com/questions/16333296/how-do-you-create-nested-dict-in-python
