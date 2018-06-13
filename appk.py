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


def main(recalc, county, applications):
    '''Main routine'''
    def split_apps(checklist):
        x = list(zip(*[(a,i+1) for i,a in enumerate(applications)
            if a['app_method'] in checklist]))
        return x if x else [[], []]

    # Check for prohibited applications
    for app in applications:
        if app['app_method'] == konstants.app_methods[0]:
            print('TIF strip shallow injection is prohibited. ' + 
                konstants.assistance)
            sys.exit()

    # Split applications into lists of tif and untarped/non-tif
    tif_methods = konstants.app_methods[1:5]
    antitif_methods = konstants.app_methods[5:]
    tif_apps, tif_apps_nums = split_apps(tif_methods)
    other_apps, other_apps_nums = split_apps(antitif_methods)

    # Check acreage, (re)calculate buffers, and print results
    lookup_table = read_tables(konstants.app_methods[1:])
    cty_type = 'coastal' if county in konstants.coastal else 'inland'
    args_cb = [cty_type, lookup_table]
    if tif_apps:
        check_acreage(tif_apps, 60, 'TIF')
        tif_buffers = [calculate_buffer(app, *args_cb) for app in tif_apps]
    else:
        tif_buffers = []
    if other_apps:
        check_acreage(other_apps, 40, 'non-TIF or untarped')
        other_buffers = [calculate_buffer(app, *args_cb) for app in other_apps]
        if recalc:
            other_buffers, other_apps = recalculate(other_apps, args_cb)
    else:
        other_buffers = []

    return list(zip(tif_buffers, tif_apps)), list(
        zip(other_buffers, other_apps)), tif_apps_nums, other_apps_nums

##### More info on... #####
# Defaultdicts:
## https://www.accelebrate.com/blog/using-defaultdict-python/
## https://stackoverflow.com/questions/16333296/how-do-you-create-nested-dict-in-python
