# -*- coding: utf-8 -*-
"""
Author: Justin Lawrence Kroes
Agency: Department of Pesticide Regulation
Branch: Environmental Monitoring
Unit: Air Program
Date: 5/4/18
"""

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

keys = [
    'app_block_size', 'product_app_rate', 'percent_active', 'app_method']

assistance = ('Please contact the California Department of Pesticide '
              'Regulation for assistance.')

mod_msg = ('NOTE: Displayed "inputs" may differ from user inputs for '
           'overlapping non-TIF or untarped application blocks. A single '
           'buffer zone is calculated based on total acreage and largest '
           'application rate, using the table for whichever of the application '
           'methods specified by the user returns the largest buffer-zone '
           'distance. The inputs listed here are the inputs used to find this '
           'buffer-zone distance.')

overlap_msg = ('Buffer zones may need to be recalculated if buffer zones for '
               'two or more applications overlap within 36 hours from the time '
               'earlier applications are complete until the start of later '
               'applications. These adjusted buffer zones can be calculated by '
               'checking this box.')

assistance2 = assistance.split()[0].lower() + ' ' + ' '.join(
    assistance.split()[1:])

app_msg = (
    'Calculate buffer zone as part of recommended permit conditions for '
    'chloropicrin and chloropicrin/1,3-D products, as outlined in Pesticide Use '
    'Enforcement Program Standards Compendium Volume 3, Restricted Materials  '
    'and Permitting, Appendix K.\n\nNote that this calculation is not valid '
    'for any products that also contain methyl bromide. If the product in '
    'question contains methyl bromide, ') + assistance2

county_msg = ('County in which the application takes place, chosen from this '
              'list of options.')

block_size_msg = ('Size of the application block, given in acres. '
                  'Application block size is limited to 60 acres for '
                  'applications using totally impermeable films (TIF) and '
                  '40 acres for non-TIF and untarped applications.')

rate_msg = (
    'Broadcast-equivalent application rate for the product, given in pounds '
    'per acre.')

percent_active_msg = (
    'Percent of chloropicrin listed on the product label, given as a number '
    'between 0 and 100 without a percentage sign.')

method_msg = 'Method of application, chosen from this list of options.'
