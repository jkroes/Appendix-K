# -*- coding: utf-8 -*-
"""
Copyright (c) 2018, California Department of Pesticide Regulation, All rights
reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""

import os
import functools
import collections
import sys
import math
import csv
import copy

app_methods = [
    'tif strip shallow injection',  # PROHIBITED METHOD
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

coastal_csv = [
    'Table1.csv', 'Table2.csv', 'Table3.csv', 'Table4.csv', 'Table5.csv',
    'Table6a.csv', 'Table7a.csv', 'Table8a.csv', 'Table9a.csv',
    'Table10a.csv', 'Table11a.csv', 'Table12.csv']

inland_csv = [
    'Table1.csv', 'Table2.csv', 'Table3.csv', 'Table4.csv', 'Table5.csv',
    'Table6b.csv', 'Table7b.csv', 'Table8b.csv', 'Table9b.csv',
    'Table10b.csv', 'Table11b.csv', 'Table12.csv']

# assistance = ('Contact the California Department of Pesticide '
#               'Regulation for assistance.')

# assistance2 = assistance.split()[0].lower() + ' ' + ' '.join(
#     assistance.split()[1:])

assistance = (
    'Please check that your inputs are correct. If the inputs are valid and '
    'the problem persists, then please contact the Department of Pesticide '
    'Regulation for Assistance')

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
    coastal_tbls = [read_tabular(csv) for csv in coastal_csv]
    inland_tbls = [read_tabular(csv) for csv in inland_csv]
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
    new['regno'] = ', '.join(str(a['regno']) for a in apps)
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
            ) + assistance

        diffs = [diff for diff in map(lambda x: param - x, indices)]
        try:
            closest_diff = max(diff for diff in diffs if diff<=0)
        except ValueError:
            print(error_msg.format(
                    strings[0],
                    truncate(param, 1),
                    strings[1],
                    strings[2],
                    indices[-1],
                    strings[1]))
            sys.exit()

        return diffs.index(closest_diff)

    # Lookup correct table for combination of application method and county
    vals, rates, acreage = lookup[app['method']][county_type]
    rate_strings = ['Broadcast equivalent application rate', 'lbs AI/acre',
         'rate']
    closest_idx_rate = closest_idx(app['broadcast'], rates, rate_strings)
    acre_strings = ['Application block size', 'acres', 'block size']
    closest_idx_acre = closest_idx(app['block'], acreage,
                                   acre_strings)
    buffer = vals[closest_idx_rate][closest_idx_acre]
    if math.isnan(buffer):  # Verify that value is not NA
        print(
            'Based on the inputs, one or more buffer zones would exceed the '
            'maximum size of half a mile. ' + assistance)
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
    if app['units'] == 'gal product / treated acre':
        rate_ai *= app['density']

    if app['broad_opt']:
        app['strip'], app['center'] = 1, 1

    broadcast = rate_ai * app['strip'] / app['center']

    return broadcast

def check_total_acreage(apps, tarp_type, limit):
    '''Individual application blocks are limited to 60 and 40 acres, resp.,
    for TIF and non-TIF/untarped apps. In addition, combined acreage is
    limited for groups of overlapping applications, to these same values.'''
    msg = (
        'Groups of overlapping {} applications are limited to {} acres in '
        'total. The total area of this group is {} acres.'
    )
    acreage = sum(app['block'] for app in apps)
    if acreage > limit:
        print(msg.format(tarp_type, limit, acreage))
        sys.exit()


def truncate(f, n):
    '''Truncates/pads a float f to n decimal places without rounding'''
    s = str(f)
    i, _, d = s.partition('.')
    return '.'.join([i, (d+'0'*n)[:n]])


def main(recalc, county, applications):
    '''Main routine'''
    for app in applications:
        # Prohibited-application check
        if app['method'] == app_methods[0]:
            print('TIF strip shallow injection is prohibited. ' +
                assistance)
            sys.exit()
        # Broadcast calculations
        app['broadcast'] = broadcast_equiv_calc(app)

    # Split applications into lists of tif and untarped/non-tif
    tif_methods = app_methods[:5]
    tif_apps = [app for app in applications if app['method'] in tif_methods]
    other_apps = [app for app in applications if app not in tif_apps]

    # Check total acreage for overlapping applications
    if recalc:
        check_total_acreage(tif_apps, 'TIF', 60)
        check_total_acreage(other_apps, 'non-TIF/untarped', 40)

    # (Re)calculate buffers; check acreage and broadcast rates against limits
    lookup_table = read_tables(app_methods[1:])
    cty_type = 'coastal' if county in coastal else 'inland'
    args_cb = [cty_type, lookup_table]

    tif_buffers = [calculate_buffer(app, *args_cb) for app in tif_apps
        ] if tif_apps else []

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
