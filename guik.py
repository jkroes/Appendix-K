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

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from io import StringIO
import functools
import sys
import contextlib
import os
import csv
import appk
import datetime
import re
from collections import namedtuple
from collections import defaultdict
from collections import OrderedDict
from collections import deque

county_msg = (
    'County in which the application(s) take place, chosen from this list of '
    'options.'
)
broad_msg = (
    'Broadcast-equivalent application rate, given in pounds or gallons of '
    'product per treated acre, where acreage treated is defined as the '
    'acreage of each treated bed bottom or strip located within the '
    'application block.'
)
mod_msg = (
    'NOTE: Displayed "inputs" may differ from user inputs for '
    'overlapping non-TIF or untarped application blocks. A single '
    'buffer zone is calculated based on total acreage and largest '
    'application rate, using the table for whichever of the '
    'application methods specified by the user returns the largest '
    'buffer-zone distance. The inputs listed here are the inputs used '
    'to find this buffer-zone distance.'
)
app_msg = (
    'Calculate buffer zone as part of recommended permit conditions '
    'for chloropicrin and chloropicrin/1,3-D products.'
)
overlap_msg = (
    'Buffer zones for two or more applications may overlap spatially '
    'within 36 hours from the end of each earlier application to the '
    'start of each subsequent application. In this event, a single '
    'buffer zone needs to be calculated for each group of overlapping '
    'applications. If this option is checked, only input applications that '
    'overlap each other. If you wish to input multiple groups of overlapping '
    'applications, run the tool once for each such group; otherwise, '
    'incorrect buffer zones may result. See the README file for more '
    'information.'
)
broad_opt_msg = (
    'Toggle this checkbox if inputting the broadcast-equivalent application '
    'rate directly. Do not toggle this checkbox if you need the broadcast '
    'rate to be calculated from the product application rate.'
)
block_msg = (
    'Size of the application block, given in acres. '
    'Application block size is limited to 60 acres for '
    'applications using totally impermeable films (TIF) and '
    '40 acres for non-TIF and untarped applications. '
    'The application block is defined by US EPA as the acreage within '
    'the perimeter of the fumigated portion of a field '
    '(including, e.g., furrows, irrigation ditches, and roadways). '
    'The perimeter of the application block is the border that '
    'connects the outermost edges of total area treated with '
    'the fumigant product. For California, an application block '
    'is also a field or the portion of a field treated in a 24-hour '
    'period that typically is identified by visible indicators, maps '
    'or other tangible means.'
)
rate_msg = (
    'Pounds or gallons of product per treated acre, where acreage treated is '
    'defined as the acreage of each treated bed bottom or strip located '
    'within the application block.'
)
strip_msg = (
    'Width of strips or bed bottoms, given in inches.'
)
center_msg = (
    'Distance between the centers of adjacent strips or beds, '
    'given in inches.'
)
regno_msg = 'Registration number, chosen from this list of options.'
method_msg = 'Method of application, chosen from this list of options.'


def center_top_level(toplevel):
    '''Center toplevel windows, including tk.Tk()

    Read note under w.winfo_geometry:
    http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/universal.html
    '''
    toplevel.update_idletasks()
    width = toplevel.winfo_width()
    height = toplevel.winfo_height()

    positionRight = int(toplevel.winfo_screenwidth()/2 - width/2)
    positionDown = int(toplevel.winfo_screenheight()/2 - height/2)

    # Positions the window in the center using 'geometry strings' with form
    # wxh+x+y, where x and y are dist away from left and top of the screen
    toplevel.geometry("+{}+{}".format(positionRight, positionDown))


def validate(choices, P):
    '''Ensure that entry conforms to predetermined choices'''
    # Typing and deleting makes for some cool printed console art! :)
    # print(P)
    for c in choices:
        if c.startswith(P):
            return True
    else:
        return False


def onFrameConfigure(canvas):
    '''Reset the scroll region to encompass the inner frame'''
    canvas.configure(scrollregion=canvas.bbox("all"))


def make_help_label(self, msg, photo, row=None, column=None):
    def show_help(event, msg):
        messagebox.showinfo('Help', msg)

    l = ttk.Label(self, image=photo)
    if row is not None and column is not None:
        l.grid(row=row, column=column, sticky='W')
    l.bind('<Button-1>', functools.partial(show_help, msg=msg))
    return l


def writeDetailsToFile():
    pass


def read_csv(dir, filename):
    with open(os.path.join(dir, filename), newline='') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        colnames = next(csvreader)
        result = defaultdict(list)
        for c in colnames:  # Initialize defaults (lists)
            result[c]
        for row in csvreader:
            if all(row):  # Omit empty rows at bottom of csv files
                for i,val in enumerate(row):
                    result[colnames[i]].append(val)
        return result


def invalid_value(W, warning):
    global root
    widget = root.nametowidget(W)
    if widget.get():  # Prevent cascading warnings
        master = widget.master
        master_type = type(master)
        if master_type == Details:
            master.mainframe._prompt(warning)
        if master_type == MainFrame:
            master._prompt(warning)
        widget.delete(0, tk.END)
        widget.focus_set()


# def counter(fn):
#     '''Wrapper to keep track of number of calls to a function'''
#     def counted(*args, **kwargs):
#         counted.ncalls += 1
#         return fn(*args, **kwargs)
#     counted.ncalls = 0
#     return counted

class Capturing(list):
    '''Capture stdout. The target of the as-clause of a with statement can
    be passed to subsequent invocations of this context manager.
    '''
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = StringIO()
        return self
    def __exit__(self, *args):
        self.append(sys.stdout.getvalue())
        sys.stdout = self._stdout


class MainFrame(ttk.Frame):
    '''Main application window'''
    counties = sorted(appk.coastal + appk.inland)
    main_text = (
        'Date of determination:',
        'Permittee name:',
        'Permittee number:',
        'Site location:',
        'County:',
        'Overlapping applications:',
        'Applications:'
    )
    details_text = OrderedDict(
        zip(
            (
                'broad_opt',
                'date',
                'block',
                'rate',
                'strip',
                'center',
                'regno',
                'method'
            ),
            (
                'Directly input broadcast-equivalent application rate:',
                'Application date (yyyy-mm-dd):',
                'Application block size (acres):',
                'Product application rate:',
                'Strip or bed-bottom width (inches):',
                'Center-to-center row spacing (inches):',
                'Registration number:',
                'Application method:'
            )
        )
    )

    try:  # http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
        base_path = sys._MEIPASS
    except:
        base_path = os.getcwd()
    products = read_csv(base_path, 'chloropicrin_products.csv')

    def __init__(self, parent, *args, **kwargs):
        '''https://stackoverflow.com/questions/4140437/interactively-
        validating-entry-widget-content-in-tkinter

        Valid percent substitutions (from the Tk entry man page)
        Note: you only have to register the ones you need

        %d = Type of action (1=insert, 0=delete, -1 for others)
        %i = index of char string to be inserted/deleted, or -1
        %P = value of the entry if the edit is allowed
        %s = value of entry prior to editing
        %S = the text string being inserted or deleted, if any
        %v = the type of validation that is currently set
        %V = the type of validation that triggered the callback
             (key, focusin, focusout, forced)
        %W = the tk name of the widget

        See http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/entry-
        validation.html for step-by-step instructions and possible values for
        validation

        For more on calling parent-class init and old-style classes, see
        http://stupidpythonideas.blogspot.com/2013/12/whats-deal-with-
        ttkframeinitself-parent.html
        '''
        def validate_county(P):
            return P in self.counties

        def invalid_county(W):
            '''Runs when validate_county returns False
            Clear county-combobox widget'''
            warning = (
                'The county you entered is invalid. Ensure that you enter '
                'a valid county or select one from the dropdown list.'
            )
            invalid_value(W, warning)

        ttk.Frame.__init__(self, parent, *args, **kwargs)

        # Create and position mainframe labels
        for i,t in enumerate(self.main_text):
            ttk.Label(self, text=t
            ).grid(row=i, column=0, columnspan=2, sticky='W')

        # Create and position useless mainframe widgets
        UselessWidgets = namedtuple(
            'UselessWidgets',
            ['date', 'permittee_name', 'permittee_num', 'site_loc']
        )
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        useless = [ttk.Label(self, text=now)] + [
            ttk.Entry(self) for _ in range(3)
        ]
        self.useless = UselessWidgets(*useless)
        for i,v in enumerate(self.useless):
            v.grid(row=i, column=2, sticky='WE')

        # Create and position mainframe county combobox
        vcmd = (self.register(validate_county), '%P')
        invcmd = (self.register(invalid_county), '%W')
        self.county = ttk.Combobox(
            self,
            values=self.counties,
            validate='focusout',
            validatecommand=vcmd,
            invalidcommand=invcmd
        )
        county_row = self.main_text.index('County:')
        self.county.grid(row=county_row, column=2, sticky='WE')

        # Create and position mainframe checkbox toggling overlap calc.
        self.overlap_var = tk.IntVar()
        self.overlap = ttk.Checkbutton(self, variable=self.overlap_var)
        overlap_row = self.main_text.index('Overlapping applications:')
        self.overlap.grid(row=overlap_row, column=2, sticky='W')
        # self.overlap.invoke()  # Toggles state of Checkbutton

        # Create, position, and bind help-labels:
        help_photo_path = os.path.join(self.base_path, 'help.gif')
        self.photo = tk.PhotoImage(file=help_photo_path
        ).subsample(30,30)
        make_help_label(
            self,
            row=county_row,
            column=3,
            msg=county_msg,
            photo=self.photo
        )
        make_help_label(
            self,
            row=overlap_row,
            column=3,
            msg=overlap_msg,
            photo=self.photo
        )

        # Create movable widgets (don't position yet)
        self.movable = {}
        self.movable['adder'] = ttk.Button(
            self,
            text='+',
            command=self.add_button
        )
        self.movable['remover'] = ttk.Button(
            self,
            text='-',
            command=self.rm_button
        )
        self.movable['submitter'] = ttk.Button(
            self,
            text='Calculate buffer zones',
            command=self._run
        )
        self.movable['submitter_help'] = make_help_label(self,
                                                         app_msg,
                                                         self.photo
                                                         )

        logo_photo_path = os.path.join(self.base_path, 'EM-Large Logo.gif')
        self.logophoto = tk.PhotoImage(file=logo_photo_path
        ).subsample(6,6)
        self.movable['logo'] = ttk.Label(self, image=self.logophoto)

        # Other instance variables
        self.root = self.winfo_toplevel()
        self.applications = []
        self.details = []

    def _hide_main(self, idx):
        '''Open window to input application-specific parameters'''
        details = self.details[idx]
        details.geometry(self.root.geometry())  # Sync windows' dimensions
        details.deiconify()  # show application window
        self.root.withdraw()  # hide main window

    def add_button(self):
        '''Create app details window, button to switch to app details window,
        and labels on main screen showing details'''
        def init_main_details(text, row, column):
            lab = ttk.Label(self, text=text)
            lab.grid(row=row, column=column, sticky='W')
            return lab

        def strip_units(s):
            return ''.join(re.split(' \(.*\)', s))

        idx = len(self.applications)
        app_number = idx + 1
        main_details = {k:v for k,v in self.details_text.items()
            if k != 'broad_opt'
        }
        button_row = len(self.main_text) + (
            idx * (len(main_details) + 1)
        )

        button = ttk.Button(
            self,
            text='Application {} details'.format(app_number),
            command=functools.partial(self._hide_main, idx)
        )
        button.grid(row=button_row, column=2, sticky='WE')
        self.applications.append(button)

        button.details_labels = OrderedDict(
            (k, init_main_details(strip_units(v), button_row+i+1, 2))
            for i, (k,v) in enumerate(main_details.items())
        )
        button.details = OrderedDict(
            (k, init_main_details('', button_row+i+1, 3))
            for i, (k,v) in enumerate(main_details.items())
        )

        self.details.append(Details(self, app_number))

        self._adjust_buttons(button_row)

    def rm_button(self):
        '''Destroy newest app button and associated widgets, if multiple
        buttons exist'''
        idx = len(self.applications)

        if idx > 1:
            button = self.applications.pop()
            button_row = len(self.main_text) + ((idx - 2) * (
                len(button.details) + 1))
            for k,v in button.details_labels.items():
                v.destroy()
                button.details[k].destroy()
            button.destroy()
            details = self.details.pop()
            details.destroy()
            self._adjust_buttons(button_row)

    def _adjust_buttons(self, row):
        '''Adjust other buttons to accommodate new/rm application button'''
        offset = row + len(self.applications[-1].details) + 1

        self.movable['adder'].grid(row=row, column=0)
        self.movable['remover'].grid(row=row, column=1)
        self.movable['submitter'].grid(
            row=offset,
            column=2,
            sticky='WE',
            pady=25
        )  # Add space between rows. (padx shirnks widget width.)
        self.movable['submitter_help'].grid(row=offset, column=3, sticky='W')
        self.movable['logo'].grid(
            row=offset+1, column=0, columnspan=4,
            sticky=tk.N+tk.E+tk.S+tk.W)

    def _run(self):
        '''Run command line script (appk.py) for buffer zone calculation'''
        def show_results(results):
            messagebox.showinfo('Buffer-zone Determination', results)

        def get_app_num(app):
            num = app['number']
            return num if isinstance(num, int) else int(num[0])

        # Extract values from main and application widgets
        recalc = True if self.overlap_var.get() else False
        county = self._verify_county()
        app_details = self._verify_details()
        if not app_details or not county:
            return

        # Pass args to appk.py and collect results
        with contextlib.suppress(SystemExit), Capturing() as out:
            apps = appk.main(recalc, county, app_details)

        # Display "error" messages
        out = ''.join(out)
        if out:  # Display error messages from appk.py
            self._prompt(out)
            return

        # Display results
        if recalc:
            show_results(mod_msg)
        apps = sorted(apps, key=get_app_num)
        rpw = 5  # results per window
        apps_split = [apps[i:i+rpw] for i in range(0, len(apps), rpw)]
        for i, group in enumerate(apps_split):
            results = self._construct_results(
                group,
                i+1,
                len(apps_split)
            )
            show_results(results)

    @staticmethod
    def _prompt(warning):
        messagebox.showwarning('Warning', warning)

    def _verify_county(self):
        '''Verify that the county has been entered (fully)'''
        county = self.county.get()
        if not county or county not in self.counties:
            warning = (
                'Please specify the county in which the '
                'application(s) will take place. Ensure that the '
                'county is fully typed out or else is selected '
                'from the dropdown.'
            )
            self._prompt(warning)
            return False
        return county

    def _verify_details(self):
        '''Verify that each application with a details window has all
        details, retrieve widget values for appk.py, use value of
        registration number to retrieve relevant values from the
        products table, and convert numeric strings to numeric'''
        def check_app_details(d, app_num):
            '''NOTE: tk.Combobox.get is in fact tk.Entry.get'''

            def check_detail(widget):
                user_input = widget.get()
                try:
                    return float(user_input)
                except ValueError:
                    return user_input

            app = {
                k:check_detail(v) for k,v in d.app_details.items()
                if k != 'broad_opt'
            }
            app['broad_opt'] = d.broad_opt_var.get()

            exclude = ['broad_opt']
            if app['broad_opt']:
                exclude += ['strip', 'center']
            if not all(v for k,v in app.items() if k not in exclude):
                return False

            prod_idx = self.products['SHOW_REGNO'].index(app['regno'])
            app['number'] = app_num
            app['density'] = float(
                self.products['Density (lb/gallon)'][prod_idx]
            )
            app['percent'] = float(
                self.products['PRODCHEM_PCT'][prod_idx]
            )
            app['name'] = self.products['PRODUCT_NAME'][prod_idx]

            return app

        warning = (
            'Application(s) {} are missing necessary details. Please fill out '
            'all of the fields listed in each application window.'
        )
        apps = [check_app_details(d, i+1) for i,d in enumerate(self.details)]
        missing = [str(i+1) for i,a in enumerate(apps) if not a]
        if missing:
            self._prompt(
                warning.format(
                    ', '.join(missing)
                )
            )
            return False
        return apps

    def _tbl_num(self, method):
        '''Return table used to determine buffer,
        as listed in Appendix K'''
        county = self.county.get()
        files = (
            appk.coastal_csv if county in appk.coastal else appk.inland_csv
        )
        file = files[appk.app_methods[1:].index(method)]
        prefix = file.split('.')[0]
        re_list = re.split('(\d+)', prefix)
        list_filt = [s for s in re_list if s]
        tbl = ''
        for i, s in enumerate(list_filt):
            if i == 1:
                tbl += ' {}'.format(s)
            else:
                tbl += s
        return tbl

    def _construct_results(self, apps, win_num=None, win_num_max=None,
        results=''):
        template = (
            'Application {}:\n'
            'Product: {}\n'
            'Buffer-zone distance: {} feet\n'
            '(Calculated using {}, a broadcast-equivalent rate '
            'of {} lbs A.I./acre and an application '
            'block of {} acres.)\n\n'
        )
        # Products spreadsheet has 3 sig digs, but only 1 shown
        for app in apps:
            results += template.format(
                app['number'],
                '{} ({})'.format(app['regno'], app['name']),
                app['buffer'],
                self._tbl_num(app['method']),
                appk.truncate(app['broadcast'], n=1),
                appk.truncate(app['block'], n=1)
            )
        if win_num and win_num_max:
            results += 'Results {} of {}'.format(
                win_num, win_num_max
            )
        return results


class Details(tk.Toplevel):
    '''Window for filling in application details'''
    def __init__(self, mainframe, app_number):
        def validate_date(P):
            '''Ensure yyyy-mm-dd format'''
            try:
                year, month, day = [int(s) for s in P.split('-')]
                datetime.date(year=year,month=month,day=day)
            except ValueError:  # Covers both not enough values
                # to unpack and invalid inputs to datetime()
                return False
            else:
                return True

        def validate_app_method(P):
            return P in appk.app_methods

        def validate_regno(P):
            return P in self.mainframe.products['SHOW_REGNO']

        def validate_entry(P):
            '''Ensure that input is numeric

            Note that this method is called twice when replacing a selection
            with input. Once, with d='0' (if %d is used as a parameter), then
            with d='1'. For this reason it is impossible to differentiate b/w
            clearing a selection for a valid input and an invalid input.
            Clearing will take place regardless, but invalid inputs will not be
            entered afterward.'''
            try:
                float(P)
            except ValueError:
                if not P:
                    return True
                return False
            else:
                return True

        def invalid_date(W):
            '''Runs when validate_date returns False
            Clear date-entry widget'''
            warning = (
                'The date you entered is invalid. Ensure that you enter '
                'a valid date in the "yyyy-mm-dd" format.'
            )
            invalid_value(W, warning)

        def invalid_app_method(W):
            warning = (
                'The application method you entered is invalid. Ensure that '
                'you enter a valid method or select one from the dropdown '
                'list.'
            )
            invalid_value(W, warning)

        def invalid_regno(W):
            warning = (
                'The registration number you entered is invalid. Ensure that '
                'you enter a valid registration number or select one from the '
                'dropdown list.'
            )
            invalid_value(W, warning)

        # @counter
        def create_custom(validate_fn, invalid_fn, widget, *args,
            **kwargs):
            '''Create non-default (or non-entry) widgets. See `entries`.'''
            vcmd = (self.register(validate_fn), '%P')
            invcmd = (self.register(invalid_fn), '%W')
            return widget(self,
                          validate='focusout',
                          validatecommand=vcmd,
                          invalidcommand=invcmd,
                          *args,
                          **kwargs
            )

        def hide():
            '''Update mainframe labels with input details and hide window.'''
            button = self.mainframe.applications[self.app_number - 1]
            apps = {k:self.app_details[k].get() for k in button.details.keys()}
            units = self.app_details['units'].get()

            apps['block'] += ' acres' if apps['block'] else ''

            if not (apps['rate'] and units):
                apps['rate'] = ''
                apps['units'] = ''
            else:
                apps['rate'] +=  ' ' + units

            apps['strip'] += ' inches' if apps['strip'] else ''
            apps['center'] += ' inches' if apps['center'] else ''

            regno = apps['regno']
            if regno:
                products = self.mainframe.products
                prod_idx = products['SHOW_REGNO'].index(regno)
                name = products['PRODUCT_NAME'][prod_idx]
                apps['regno'] += ' ' + '({})'.format(name)

            if self.broad_opt_var.get():
                apps['strip'] = 'N/A'
                apps['center'] = 'N/A'

            for k,v in button.details.items():
                v.configure(text=apps[k])

            self.mainframe.root.geometry(self.geometry())
            self.mainframe.root.deiconify()  # show main frame
            self.withdraw()

        def cb_cmd(button, toggle=[False]):
            '''Modify app to reflect direct input of broadcast rate'''
            toggle[0] = not toggle[0]

            app = self.app_details
            strip, center = app['strip'], app['center']
            if toggle[0]:
                strip.delete(0, tk.END)
                center.delete(0, tk.END)
                state = 'disabled'
                text = 'Broadcast-equivalent application rate:'
                msg = broad_msg
            else:
                state = 'normal'
                text = self.mainframe.details_text['rate']
                msg = self.details_msgs['rate']

            strip.configure(state=state)
            center.configure(state=state)
            self.labels['rate'].configure(text=text)
            button.details_labels['rate'].configure(text=text)
            row = list(self.mainframe.details_text.keys()).index('rate')
            self.help['rate'] = make_help_label(self,
                                                row=row,
                                                column=2,
                                                msg=msg,
                                                photo=self.mainframe.photo
                                                )

        # Configure window properties
        if sys.platform == 'darwin':  # http://wiki.tcl.tk/44444
            tk.Toplevel.__init__(self, background='#e6e6e6')
        else:
            tk.Toplevel.__init__(self)

        # Since tk displays newly created windows, hide this window until
        # user clicks the associated application button on main screen
        self.withdraw()

        # Constants and attributes
        self.mainframe = mainframe
        self.title('Appendix K - Application {} Details'.format(app_number))
        self.app_number = app_number

        # Create and position label widgets
        self.labels = OrderedDict((k, ttk.Label(self, text=v) )
            for k,v in self.mainframe.details_text.items())
        for i,v in enumerate(self.labels.values()):
            v.grid(row=i, column=0, sticky='W')

        # Create and position non-label widgets
        # ncustom = create_custom.ncalls
        details_keys = self.mainframe.details_text.keys()
        app_details = OrderedDict.fromkeys(details_keys)
        self.broad_opt_var = tk.IntVar()
        cb_cmd = functools.partial(cb_cmd,
            button=self.mainframe.applications[app_number-1])
        app_details['broad_opt'] = ttk.Checkbutton(self,
            variable=self.broad_opt_var, command=cb_cmd)
        app_details['date'] = create_custom(validate_date, invalid_date,
            ttk.Entry)
        app_details['regno'] = create_custom(validate_regno, invalid_regno,
            ttk.Combobox, width=40, values=mainframe.products['SHOW_REGNO'])
        app_details['method'] = create_custom(validate_app_method,
            invalid_app_method, ttk.Combobox, width=40,
            values=appk.app_methods)
        vcmd = (self.register(validate_entry), '%P')
        for i,k in enumerate(details_keys):
            if k not in ('broad_opt', 'date', 'regno', 'method'):
                app_details[k] = ttk.Entry(self, validate='key',
                    validatecommand=vcmd)
            app_details[k].lift()  # Fix tab order (defaults to creation order)
            app_details[k].grid(row=i, column=1, sticky='WE')
        self.app_details = app_details

        # Create and position combox widget for app-method units selection
        self.app_details['units'] = ttk.Combobox(self, width=21,
            values=('lbs product / treated acre',
                    'gal product / treated acre'))
        row = list(details_keys).index('rate')
        self.app_details['units'].grid(row=row, column=3)

        # Create and position navigation button to main screen
        ttk.Button(self,
                   text='Save and return to main window',
                   command=hide
                   ).grid(row=len(self.app_details), column=1, pady=20)

        # Create and position help labels for inputs
        self.details_msgs = OrderedDict(
            zip(
                (k for k in mainframe.details_text.keys() if k != 'date'),
                (
                    broad_opt_msg,
                    block_msg,
                    rate_msg,
                    strip_msg,
                    center_msg,
                    regno_msg,
                    method_msg
                )
            )
        )
        self.help = OrderedDict()
        for k,v in self.details_msgs.items():
            row = list(details_keys).index(k)
            self.help[k] = make_help_label(self,
                                           row=row,
                                           column=2,
                                           msg=v,
                                           photo=mainframe.photo
                                           )
        # Logo
        self.logo = ttk.Label(self, image=self.mainframe.logophoto)
        self.logo.grid(
            row=len(self.app_details)+10,
            column=0,
            columnspan=4,
            sticky=tk.N+tk.E+tk.S+tk.W)

#==============================================================================
# Spawn a TCL interpreter
#==============================================================================
root = tk.Tk()
root.title('Appendix K (v1.0.0)')
root.geometry("720x500")
center_top_level(root)

#==============================================================================
# Create a "scrollable window"
#
# (See 'Tkinter 8.5 reference: a GUI for Python' and
#  https://stackoverflow.com/questions/3085696/adding-a-scrollbar-to-a-group-
#  of-widgets-in-tkinter for details)
#
# NOTE: Wihout a window anchor, the frame will move down after
# deleting all added rows by a distance proportional to the number of rows
#==============================================================================
# http://wiki.tcl.tk/44444
canvas = tk.Canvas(root, borderwidth=0, background='#e6e6e6')\
    if sys.platform == 'darwin' else tk.Canvas(root, borderwidth=0)
frame = MainFrame(canvas)
frame.add_button()  # Button for a single application window
# Function is triggered whenever the frame changes size (or location on some platforms)
frame.bind(
    "<Configure>",
    lambda event, canvas=canvas: onFrameConfigure(canvas)
)

vsb = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
vsb.pack(side="right", fill="y")

canvas.configure(yscrollcommand=vsb.set)
canvas.pack(side="left", fill="both", expand=True)
canvas.create_window((4, 4), window=frame, anchor='nw')

#==============================================================================
# Inform the user that the tool is intended only for chloropicrin use
#==============================================================================
msg = (
    'This tool for testing purposes only and results from the tool should be '
    'evaluated prior to release.  This tool only applies  to the application '
    'of products that contain 2% or more of chloropicrin.\n\n'
    'This tool is based on CDPR\'s "Pesticide Use Enforcement Program '
    'Standards Compendium, Volume 3, Appendix K: Chloropicrin and '
    'Chloropicrin in Combination with Other Products (Field Fumigant) '
    'Recommended Permit Conditions (41st Revision - December 2017)," as well '
    'as the information at the following web page referenced by Appendix K: '
    'https://www.cdpr.ca.gov/chloropicrin.htm.\n\n'
    'For questions or feedback about this tool, please contact:\n\n'
    'Minh Pham\n(916) 445-0979\nMinh.Pham@cdpr.ca.gov'
)
messagebox.showinfo('Help', msg)

#==============================================================================
# Set top window properties
#==============================================================================
# # Get size of usable screen. (A bit of a hack.)
# root.attributes('-alpha', 0)
# root.state('zoomed')
# root.update()  # Otherwise we will see maxw, maxh = 1, 1
# maxw = root.winfo_width()
# maxh = root.winfo_height()

# # Reset attributes and configure geometry
# swidth=vsb.winfo_width()
# root.state('normal')  # NOTE: This is what causes the vanishing title bar effect
# starting_size = "710x500+0+0"
# # root.geometry(starting_size)
# # center_top_level(root)
# print(swidth)
# root.geometry('{}x{}+0+0'.format(maxw-swidth, maxh))
# root.attributes('-alpha', 1)

#==============================================================================
# Run event loop / spawn the application
#==============================================================================
root.mainloop()

#==============================================================================
# RANDOM DEVELOPER NOTES
#==============================================================================
# Assert statements raise errors if the specified condition evaluates
# to false while __debug__. Note that __debug__ is true under normal
# circumstances. Disable them with the '-O' flag.

# Classes
#
# Classmethod
# A class method receives the class as implicit first argument. See
# builtin functions
#
# Static methods
# A method that does not receieve an implicit first argument
#
# Inheritance
#
#class x():
#    def __init__(self, x):
#        self.x = x
#class y(x):
#    def __init__(self, y):
#        super().__init__(0)
#        self.y = y
#test = y(1)
#dir(test)[-2:]
#test.x
#test.y
#
# Check mro:
# y.__mro__

# Decorators: A function that returns another function
#
#Example:
#@f1(arg)
#@f2
#def func(): pass
#
# Equivalent to:
#def func(): pass
#func = f1(arg)(f2(func))

# What I learned while coding:
# functools.partial behaves like staticmethod:
#    _validate_county = functools.partial(
#        lambda choices, S: True if S in choices else False, counties)
#
# Class bodies are evaluated instantly so any references to variables need to
# be resolved before the class definition. References within methods, though,
# can be to variables created anytime before the method is called.
#
# Context managers are defined by 2 main methods:
# The with statement will bind this method’s return value to the
# target(s) specified in the as clause of the statement, if any.
# --Python Data Model / Python Std Lib, Chapter 4.11: Context Manager Types
#
# The context manager’s __exit__() method is invoked. If an exception
# caused the suite to be exited, its type, value, and traceback are passed
# as arguments to __exit__(). Otherwise, three None arguments are supplied.
#
# If the suite was exited due to an exception, and the return value from
# the __exit__() method was false, the exception is reraised. If the
# return value was true, the exception is suppressed, and execution
# continues with the statement following the with statement.
#
# If the suite was exited for any reason other than an exception, the
# return value from __exit__() is ignored, and execution proceeds at the
# normal location for the kind of exit that was taken.
# --Python Language Reference, Chapter 8: Compound Statements

# FUTURE LEARNING IN DEPTH
#
# How to use partialmethod
#
# Descriptors: https://docs.python.org/3/reference/datamodel.html#descriptors
#   Note in linke above that staticmethod and classmethod are descriptors, not callables!
#   See https://stackoverflow.com/questions/36922532/python-functools-partial-how-to-apply-it-to-a-class-method-with-the-static-dec
#
# Callables
#   Partials are callable: https://docs.python.org/3/library/functools.html#partial-objects
#   Partialmethods however are descriptors
#
# Review list of builtin decorators, as well as context managers in contextlib
