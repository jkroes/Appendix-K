# -*- coding: utf-8 -*-
"""
Author: Justin Lawrence Kroes
Agency: Department of Pesticide Regulation
Branch: Environmental Monitoring
Unit: Air Program
Date: 4/30/18
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
import konstants
import appk
import datetime
import re
from collections import namedtuple
from collections import defaultdict
from collections import OrderedDict
from collections import deque


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


def make_help_label(self, row, column, msg, photo):
    def show_help(event, msg):
        messagebox.showinfo('Help', msg)

    l = ttk.Label(self, image=photo)
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
    counties = sorted(konstants.coastal + konstants.inland)
    details_keys = ('date', 'block', 'rate', 'strip', 'center', 'area',
        'regno', 'method')
    details_text = OrderedDict(zip(details_keys, (
        'Application date (yyyy-mm-dd):',
        'Application block size (acres):',
        'Product application rate (using treated acreage):',
        'Strip or bed bottom width (inches):',
        'Center-to-center row spacing (inches):',
        'Area of strips or bed bottoms and rows (acres):',
        'Registration Number:',
        'Application method:')))
    # main_keys = ['date', 'name', 'number', 'loc', 'county', 'overlap', 'apps']
    main_text = [
        'Date of Determination:',
        'Permittee Name:',
        'Permittee Number:',
        'Site Location:',
        'County:',
        'Overlapping applications:',
        'Applications:']

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

        For more on calling parent-class init, see
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
                'a valid county or select one from the dropdown list.')
            invalid_value(W, warning)

        ttk.Frame.__init__(self, parent, *args, **kwargs)

        # Create and position mainframe labels
        for i,t in enumerate(self.main_text):
            ttk.Label(self, text=t).grid(
                    row=i, column=0, columnspan=2, sticky='W')

        # Create and position useless mainframe widgets
        UselessWidgets = namedtuple('UselessWidgets',
            ['date', 'permittee_name', 'permittee_num', 'site_loc'])
        now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
        useless = [ttk.Label(self, text=now)] + [
            ttk.Entry(self) for _ in range(3)]
        self.useless = UselessWidgets(*useless)
        for i,v in enumerate(self.useless):
            v.grid(row=i, column=2, sticky='WE')

        # Create and position mainframe county combobox
        vcmd = (self.register(validate_county), '%P')
        invcmd = (self.register(invalid_county), '%W')
        self.county = ttk.Combobox(self, values=self.counties, validate='focusout',
            validatecommand=vcmd, invalidcommand=invcmd)
        county_row = self.main_text.index('County:')
        self.county.grid(row=county_row, column=2, sticky='WE')

        # Create and position mainframe checkbox toggling overlap calc.
        self.overlap_var = tk.IntVar()
        self.overlap = ttk.Checkbutton(self, variable=self.overlap_var)
        overlap_row = self.main_text.index('Overlapping applications:')
        self.overlap.grid(row=overlap_row, column=2, sticky='W')
        # self.overlap.invoke()  # Toggles state of Checkbutton

        # Create, position, and bind help-labels:
        photo_path = os.path.join(self.base_path, 'help.gif')
        self.photo = tk.PhotoImage(file=photo_path).subsample(30,30)
        make_help_label(self, row=county_row, column=3, msg=konstants.county_msg, photo=self.photo)
        make_help_label(self, row=overlap_row, column=3, msg=konstants.overlap_msg, photo=self.photo)

        # Create movable action buttons (don't position yet)
        self.movable = {}
        self.movable['adder'] = ttk.Button(self, text='+', command=self.add_button)
        self.movable['remover'] = ttk.Button(self, text='-', command=self.rm_button)
        self.movable['submitter'] = ttk.Button(self, text='Calculate buffer zones',
            command=self._run)

        # Other instance variables
        self.root = self.winfo_toplevel()
        self.applications = []
        self.details = []

    def add_button(self):
        '''Add button for an application, provided details have been added'''
        def hide_main(self, idx):
            '''Open window to input application-specific parameters'''
            self.details[idx].geometry(self.root.geometry())
            self.details[idx].deiconify()  # show application window
            self.root.withdraw()

        # Create application button
        idx = len(self.applications)
        app_number = idx + 1
        text = 'Application {} Details'.format(app_number)
        button = ttk.Button(
            self, text=text, command=functools.partial(hide_main, self, idx))
        self.applications.append(button)

        # Create Details object. Note that it will update button.details'
        # text with inputs when it is hidden
        self.details.append(
            Details(self, app_number))
        button.details_labels = [ttk.Label(self, text=v) for _,v in self.details_text.items()]
        button.details = [ttk.Label(self, text='') for _ in self.details_text.keys()]

        # Display new button and (initially empty) inputs underneath
        button_row = len(self.main_text) + (idx * (len(self.details_text) + 1))
        button.grid(row=button_row, column=2, sticky='WE')
        for i, dl in enumerate(button.details_labels):
            dl.grid(row=button_row + i + 1, column=2, sticky='W')
            button.details[i].grid(
                row=button_row + i + 1, column=3, sticky='W')

        self._adjust_buttons(button_row)  # Adjust movable buttons

    def rm_button(self):
        '''Remove newest app button and associated widgets, if multiple
        buttons exist'''
        idx = len(self.applications)
    
        if idx > 1:
            # Destroy all objects for this application
            button = self.applications.pop()
            for i, dl in enumerate(button.details_labels):
                dl.destroy()
                button.details[i].destroy()
            button.destroy()
            details = self.details.pop()
            details.destroy()

            # Adjust movable buttons
            button_row = len(self.main_text) + ((idx - 2) * (len(self.details_text) + 1))
            self._adjust_buttons(button_row)

    def _adjust_buttons(self, row):
        '''Adjust other buttons to accommodate new/rm application button'''
        offset = row + len(self.details_text) + 1

        # Movable action buttons
        self.movable['adder'].grid(row=row, column=0)
        self.movable['remover'].grid(row=row, column=1)
        self.movable['submitter'].grid(row=offset, column=2, sticky='WE',
            pady=25)  # Add space between rows. (padx shirnks widget width.)

        # The only help button that moves around
        if not hasattr(self, 'submitter_help'): 
            self.submitter_help = make_help_label(  
                self, row=offset, column=3, msg=konstants.app_msg, photo=self.photo)
        else:
            self.submitter_help.grid(row=offset, column=3, sticky='W')
            
        # DPR Logo
        if not hasattr(self, 'logo'):
            photo_path = os.path.join(self.base_path, 'dprlogo_3.gif')
            self.logophoto = tk.PhotoImage(file=photo_path).subsample(3,3)
            self.logo = ttk.Label(self, image=self.logophoto)
        self.logo.grid(row=offset+1, column=0, columnspan=4, sticky='EW')

    def _run(self):
        '''Run command line script (appk.py) for buffer zone calculation

        NOTE: tkinter.Entry.get is the method used by all widgets
        NOTE: argparse.ArgumentParser.parse_args requires a flat list
        '''
        def show_results(results):
            messagebox.showinfo('Buffer Zone Determination', results)

        def get_app_num(app):
            num = app['number']
            return num if isinstance(num, int) else int(num[0])

        def split_list(li, length):
            return [li[i:i+rpw] for i in range(0, len(li), length)]

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
            show_results(konstants.mod_msg)
        apps = sorted(apps, key=get_app_num)
        rpw = 3  # results per window
        split_list_rpw = functools.partial(split_list, length=rpw)
        apps_split = split_list_rpw(apps)
        for i,group in enumerate(apps_split):
            results = self._construct_results(
                group, i+1, len(apps_split))
            show_results(results)

    @staticmethod
    def _prompt(warning):
        messagebox.showwarning('Warning', warning)

    def _verify_county(self):
        '''Verify that the county has been entered (fully)'''
        county = self.county.get()
        if not county or county not in self.counties:
            warning = ('Please specify the county in which the '
                    'application(s) will take place. Ensure that the '
                    'county is fully typed out or else is selected '
                    'from the dropdown.')
            self._prompt(warning)
            return False
        return county

    def _verify_details(self):
        '''Verify that each application with a details window has all
        details, retrieve widget values for appk.py, use value of
        registration number to retrieve relevant values from the 
        products table, and convert numeric strings to numeric'''
        warning = (
            'Applications {} are missing necessary '
            'details. Please fill out all of the fields '
            'listed in each application window.')    
        
        def check_app_details(widgets_dict, app_num):
            '''NOTE: tk.Combobox.get is in fact tk.Entry.get'''

            def check_detail(widget):
                user_input = tk.Entry.get(widget)
                try:
                    return float(user_input)
                except ValueError:
                    return user_input

            app = {k:check_detail(v) for k,v in widgets_dict.items()}

            if not all(app.values()):
                return False

            prod_idx = self.products['SHOW_REGNO'].index(app['regno'])
            app['number'] = app_num
            app['density'] = float(
                self.products['Density (lb/gallon)'][prod_idx])
            app['percent'] = float(
                self.products['PRODCHEM_PCT'][prod_idx])
            app['name'] = self.products['PRODUCT_NAME'][prod_idx]

            return app
        
        apps = [check_app_details(d.app_details, i+1) 
            for i,d in enumerate(self.details)]
        missing = [str(i+1) for i,a in enumerate(apps) if not a]
        if missing:
            self._prompt(
                warning.format(
                    ', '.join(missing)))
            return False

        return apps

    def _tbl_num(self, method):
        '''Return table used to determine buffer,
        as listed in Appendix K'''
        county = self.county.get()
        files = (konstants.coastal_csv if county in konstants.coastal
            else konstants.inland_csv)
        file = files[konstants.app_methods[1:].index(method)]
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

    def _construct_results(self, apps, win_num=None, win_num_max=None, results=''):
        template = (
            'Application {}:\n'
            'Product Name: {}\n'
            'Buffer zone distance: {} feet\n'
            '(Calculated using {}, a broadcast-equivalent rate '
            'of roughly {} lbs A.I./acre and an application '
            'block of roughly {} acres.)\n\n')

        for app in apps:
            results += template.format(
                app['number'],
                app['name'],
                app['buffer'],
                self._tbl_num(app['method']),
                konstants.truncate(app['broadcast'], n=1),
                konstants.truncate(app['block'], n=1))

        if win_num and win_num_max:
            results += 'Results {} of {}'.format(
                win_num, win_num_max)
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
            return P in konstants.app_methods

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
                'a valid date in the "yyyy-mm-dd" format.')
            invalid_value(W, warning)

        def invalid_app_method(W):
            warning = (
                'The application method you entered is invalid. Ensure that you enter '
                'a valid method or select one from the dropdown list.')
            invalid_value(W, warning)

        def invalid_regno(W):
            warning = (
                'The registration number you entered is invalid. Ensure that you enter '
                'a valid registration number or select one from the dropdown list.')
            invalid_value(W, warning)

        # Configure window properties
        if sys.platform == 'darwin':  # http://wiki.tcl.tk/44444
            tk.Toplevel.__init__(self, background='#e6e6e6')
        else:
            tk.Toplevel.__init__(self)

        # Since tk displays newly created windows, hide this window until
        # user clicks the associated application button on main screen
        self.withdraw()

        self.mainframe = mainframe
        self.title('Appendix K - Application {} Details'.format(app_number))
        self.app_number = app_number

        keys = [k for k in self.mainframe.details_keys if k != 'date']
        self.msgs = OrderedDict(zip(keys, [
            konstants.block_size_msg,
            konstants.rate_msg,
            konstants.strip_msg,
            konstants.center_msg,
            konstants.area_msg,
            konstants.regno_msg,
            konstants.method_msg]))

        # Create and position label widgets
        for i, v in enumerate(mainframe.details_text.values()):
            ttk.Label(self, text=v).grid(row=i, column=0, sticky='W')

        # Create date entry
        custom_details = 0
        vcmd = (self.register(validate_date), '%P')
        invcmd = (self.register(invalid_date), '%W')
        date = ttk.Entry(self, validate='focusout', validatecommand=vcmd,
            invalidcommand=invcmd)
        custom_details += 1

        # Create combobox widget for registration-number input
        vcmd = (self.register(validate_regno), '%P')
        invcmd = (self.register(invalid_regno), '%W')
        regno = ttk.Combobox(self,
                             width=40,
                             values= mainframe.products['SHOW_REGNO'],
                             validate='focusout',
                             validatecommand=vcmd,
                             invalidcommand=invcmd)
        custom_details += 1

        # Create combobox widget for application-method input
        vcmd = (self.register(validate_app_method), '%P')
        invcmd = (self.register(invalid_app_method), '%W')
        app_method = ttk.Combobox(self,
                                  width=40,
                                  values=konstants.app_methods,
                                  validate='focusout',
                                  validatecommand=vcmd,
                                  invalidcommand=invcmd)
        custom_details += 1

        # Create entry widgets for all but one input (see below)
        vcmd = (self.register(validate_entry), '%P')
        entries = [ttk.Entry(self, validate='key', validatecommand=vcmd)
            for _ in range(len(mainframe.details_text)-custom_details)]

        # Collect (i.e., into a OrderedDict) and position widgets
        entries.insert(mainframe.details_keys.index('date'), date)
        entries.insert(mainframe.details_keys.index('regno'), regno)
        entries.insert(mainframe.details_keys.index('method'), app_method)
        for e in entries:  # Fix tab order (defaults to creation order)
            e.lift()
        self.app_details = OrderedDict(zip(
            mainframe.details_text.keys(),
            entries))
        for i, v in enumerate(self.app_details.values()):
            v.grid(row=i, column=1, sticky='WE')

        # Create and position help labels for inputs
        for k,v in self.msgs.items():
            i = mainframe.details_keys.index(k)
            make_help_label(self, row=i, column=2, msg=v,
                photo=mainframe.photo)

        # Create and position combox widget for app-method units selection
        self.app_details['units'] = ttk.Combobox(
            self, width=20, values=('lbs/acre', 'gal/acre'))
        row=list(self.app_details.keys()).index('rate')
        self.app_details['units'].grid(row=row, column=3)

        # Create and position navigation button to main screen
        ttk.Button(self, text='Save and Return to main screen', command=self._hide
                   ).grid(row=len(self.app_details), column=1, pady=20)

    def _hide(self):
        '''Update mainframe labels with input details and hide window.'''
        idx = self.app_number - 1
        button = self.mainframe.applications[idx]
        ad_values = [v.get() if k != 'rate'
            else v.get() + ' ' + self.app_details['units'].get()
            for k,v in self.app_details.items()]

        for i, d in enumerate(button.details):
            d.configure(text=ad_values[i])

        self.mainframe.root.geometry(self.geometry())
        # w, h = root.winfo_screenwidth(), root.winfo_screenheight()
        # self.mainframe.root.geometry('{}x{}+0+0'.format(w, h))
        self.mainframe.root.deiconify()  # show main frame
        self.withdraw()


#==============================================================================
# Spawn a TCL interpreter
#==============================================================================
root = tk.Tk()
root.title('Appendix K (Version June 2018)')
root.geometry("710x500")
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
if sys.platform == 'darwin':  # http://wiki.tcl.tk/44444
    canvas = tk.Canvas(root, borderwidth=0, background='#e6e6e6')
else:
    canvas = tk.Canvas(root, borderwidth=0)

frame = MainFrame(canvas)
frame.add_button()  # Button for a single application window
# Function is triggered whenever the frame changes size (or location on some platforms)
frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

vsb = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
vsb.pack(side="right", fill="y")

canvas.configure(yscrollcommand=vsb.set)
canvas.pack(side="left", fill="both", expand=True)
canvas.create_window((4, 4), window=frame, anchor='nw')

#==============================================================================
# Inform the user that the tool is intended only for chloropicrin use
#==============================================================================
msg = ('NOTE: This tool is only for applications of products with a chloropicrin '
    'content of 2% or more, products containing chloropicrin and another fumigant, '
    'or simultaneous applications of chloropicrin and another fumigant.\n\n'
    'This tool is based on CDPR\'s "Pesticide Use Enforcement Program Standards '
    'Compendium, Volume 3, Appendix K: Chloropicrin and Chloropicrin in '
    'Combination with Other Products (Field Fumigant) Recommended Permit Conditions '
    '(41st Revision - December 2017)," as well as the information at the following '
    'web page referenced by Appendix K: https://www.cdpr.ca.gov/chloropicrin.htm.')
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
