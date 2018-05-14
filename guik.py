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
import functools
import sys
from io import StringIO
import contextlib
import argparse
import konstants
import appk
import os


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
    '''Ensure that entry is valid county'''
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


def show_help(event, msg):
    messagebox.showinfo('Help', msg)


def make_help_label(self, row, msg, photo):
    l = ttk.Label(self, image=photo)
    l.grid(row=row, column=3, sticky='W')
    l.bind('<Button-1>', functools.partial(show_help, msg=msg))
    return l


def readDetailsFromFile():
    pass


def writeDetailsToFile():
    pass

def disable_mod_msg():
    pass


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
        ttk.Frame.__init__(self, parent, *args, **kwargs)

        # Create and position mainframe labels
        texts = ['County:', 'Overlapping applications:', 'Applications:']
        for i,t in enumerate(texts):
            ttk.Label(self, text=t).grid(
                    row=i, column=0, columnspan=2, sticky='W')

        # Create and position mainframe county combobox
        vcmd = (self.register(self._validate_county), '%P')
        self.county = ttk.Combobox(self, values=self.counties, validate='key',
            validatecommand=vcmd)
        self.county.grid(row=0, column=2, sticky='WE')

        # Create and position mainframe checkbox toggling overlap calc.
        self.var = tk.IntVar()
        self.overlap = ttk.Checkbutton(self, variable=self.var)
        self.overlap.grid(row=1, column=2, sticky='W')
        # self.overlap.invoke()  # Toggles state of Checkbutton

        # Create, position, and bind help labels:
        try:  # http://effbot.org/pyfaq/why-do-my-tkinter-images-not-appear.htm
            base_path = sys._MEIPASS
        except:
            base_path = os.path.abspath('.')
        photo_path = os.path.join(base_path, 'help.gif')
        self.photo = tk.PhotoImage(file=photo_path).subsample(30,30)
        msgs = [konstants.county_msg, konstants.overlap_msg]
        for i in range(0, 2):
            make_help_label(self, row=i, msg=msgs[i], photo=self.photo)

        # Create movable action buttons (don't position yet)
        self.adder = ttk.Button(self, text='+', command=self.add_button)
        self.remover = ttk.Button(self, text='-', command=self.rm_button)
        self.submitter = ttk.Button(self, text='Calculate buffer zones',
            command=self._run)

        # Other instance variables
        self.root = self.winfo_toplevel()
        self.applications = []
        self.details = {}  # !Dict is necessary b/c details are only added as
        # application buttons are clicked, meaning order and even existence
        # are not guaranteed at deletion time (see rm_button)

    def add_button(self):
        '''Add button for an application'''
        row = len(self.applications) + 3
        text = 'Application {} Details'.format(str(row-2))
        button = ttk.Button(self, text=text,
            command=lambda idx=len(self.applications): self._add_details(idx))
        self.applications.append(button)
        button.grid(row=row, column=2, sticky='WE')
        self._adjust_buttons(row)

    def rm_button(self):
        '''Remove button for an application'''
        print(list(range(len(self.applications))))
        print(self.details.keys())
        idx = len(self.applications) - 1
        if idx > 0:
            self._adjust_buttons(idx+2)
        self.applications[idx].destroy()
        self.applications.pop()
        if self.details.get(idx):  # dict.get(), not widget.get()
            win = self.details.pop(idx)
            win.destroy()
        print(list(range(len(self.applications))))
        print(self.details.keys())
        print('\n')

    def _adjust_buttons(self, row):
        '''Adjust other buttons to accommodate a new application button'''
        self.adder.grid(row=row, column=0)
        self.remover.grid(row=row, column=1)
        self.submitter.grid(row=row+1, column=2, sticky='WE',
            pady=25)  # Add space between rows. (padx shirnks widget width.)
        if not hasattr(self, 'submitter_help'):  # The only help button that
            self.submitter_help = make_help_label(  # moves around
                self, row=row+1, msg=konstants.app_msg, photo=self.photo)
        else:
            self.submitter_help.grid(row=row+1, column=3, sticky='W')

    def _add_details(self, idx):
        '''Open window to input application-specific parameters'''
        self.hide()
        if not self.details.get(idx):  # dict.get(), not widget.get()
            self.details[idx] = Details(self, idx+1)
            # NOTE: Instantiation will show window automatically
        else:
            self.details[idx].show()

    def _run(self):
        '''Run command line script (appk.py) for buffer zone calculation

        NOTE: tkinter.Entry.get is the method used by all widgets
        NOTE: argparse.ArgumentParser.parse_args requires a flat list
        '''

        def tbl_num(method, county):
            '''Return table used to determine buffer, as listed in Appendix K'''
            csvs = (konstants.coastal_csv if county in konstants.coastal
                else konstants.inland_csv)
            csv = csvs[konstants.app_methods[1:].index(method)]
            return csv.split('.')[0]

        # Verify each application is associated with a details window
        if len(self.applications) != len(self.details):
            self._prompt_add_details()
            return

        app_args = [['--app-details'] + [tk.Entry.get(i) for i in [
            d.app_block_size, d.app_rate, d.percent_active, d.app_method]
            ] for d in self.details.values()]

        # Verify that each application with a details window has all details
        for app_arg in app_args:
            if not all(app_arg):
                self._prompt_add_all_details()
                return
            # Verify that application method has been fully entered
            if app_arg[-1] not in konstants.app_methods:
                self._prompt_specify_method()
                return

        # Verify that the county has been entered (fully)
        county = self.county.get()
        if not county or county not in self.counties:
            self._prompt_add_county()
            return

        # Process arguments and feed to buffer-zone-calculation routine in
        # appk.py, capturing and displaying errors on stdout or else results
        # template2 = ('Buffer-zone distance: {} feet. This was caculated '
        #      'using {}. The table was selected from county ({}) and '
        #      'application method ({}). Buffer-zone distance was '
        #      'selected using application rate ({} lbs A.I./acre) '
        #      'and application-block size ({} acres).')
        template = ('Buffer zone distance: {} feet\n'
                    '(Calculated using {}.)\n\n'
                    'Application details:\n\n'
                    'Application block size (acres):\n{}\n'
                    'Application rate (lbs A.I./acre):\n{}\n'
                    'Application method:\n{}\n')
        args = ['--county', county] + [elem for li in app_args for elem in li]
        args = ['--recalc'] + args if self.var.get() else args
        parsed_args = appk.parse_arguments(
            konstants.app_methods, konstants.inland + konstants.coastal, args)
        with contextlib.suppress(SystemExit), Capturing() as out:
            tif, other = appk.main(parsed_args)
        out = ''.join(out)
        if out:
            self._prompt(out)
        else:
            if self.var.get():
                self._show_results(konstants.mod_msg)
            for t in tif + other:
                method = t[1]['app_method']
                self._show_results(
                        template.format(
                            t[0],
                            tbl_num(method, county),
                            t[1]['app_block_size'],
                            t[1]['product_app_rate'] * t[1]['percent_active']\
                                / 100,
                            method))

    def hide(self):
        self.root.withdraw()

    def show(self):
        # self.root.update()
        self.root.deiconify()

    @staticmethod
    def _show_results(result):
        messagebox.showinfo('Buffer Zone Determination', result)

    @staticmethod
    def _prompt(warning):
        messagebox.showwarning('Warning', warning)

    def _prompt_add_county(self):
        warning = ('Please specify the county in which the application(s) will '
                    'take place. Ensure that the county is fully typed out or '
                    'else is selected from the dropdown.')
        self._prompt(warning)

    def _prompt_add_details(self):
        warning = ('There are applications for which details have not been '
                   'added. Please add details for each application or remove '
                   'unnecessary applications.')
        self._prompt(warning)

    def _prompt_add_all_details(self):
        warning = ('Some applications are missing necessary details. Please '
                   'fill out all of the fields listed in each application '
                   'window.')
        self._prompt(warning)

    def _prompt_specify_method(self):
        warning = ('Ensure that the application method for each application '
                   'is fully typed out or else is selected from the '
                   'dropdown.')
        self._prompt(warning)

    counties = sorted(konstants.coastal + konstants.inland)
    _validate_county = functools.partial(validate, counties)


class Details(tk.Toplevel):
    '''Window for filling in application details'''
    def __init__(self, mainframe, app_number):
        # Configure window properties
        if sys.platform == 'darwin':  # http://wiki.tcl.tk/44444
            tk.Toplevel.__init__(self, background='#e6e6e6')
        else:
            tk.Toplevel.__init__(self)
        self.mainframe = mainframe
        self.geometry(mainframe.root.geometry())
        self.title('Appendix K - Application {} Details'.format(app_number))

        # Create and position label widgets
        texts = ['Application block size (acres):',
                'Product application rate (lbs/acre):',
                'Percent active ingredient:',
                'Application method:']
        [ttk.Label(self, text=t).grid(row=i, column=0, sticky='W')
            for i, t in enumerate(texts)]  # The list itself isn't needed

        # Create entry widgets
        vcmd = (self.register(self._validate_entry), '%P', '%S')
        self.app_block_size, self.app_rate, self.percent_active = [
            ttk.Entry(self, validate='key', validatecommand=vcmd)
            for _ in range(0, 3)]

        # Create combobox widget
        vcmd_meth = (self.register(self._validate_method), '%P')
        self.app_method = ttk.Combobox(self,
                                       width=40,
                                       values=konstants.app_methods,
                                       validate='key',
                                       validatecommand=vcmd_meth)

        # Position entry and combobox widgets
        self.app_block_size.grid(row=0, column=1, sticky='WE')
        self.app_rate.grid(row=1, column=1, sticky='WE')
        self.percent_active.grid(row=2, column=1, sticky='WE')
        self.app_method.grid(row=3, column=1, sticky='WE')

        # Create and position help labels
        msgs = [konstants.block_size_msg, konstants.rate_msg,
                konstants.percent_active_msg, konstants.method_msg]
        for i in range(0, 4):
            make_help_label(self, row=i, msg=msgs[i],
                photo=self.mainframe.photo)

        # Create and position window navigation button
        ttk.Button(self, text='Return to main screen', command=self._close
                   ).grid(row=4, column=1, pady=20)

    @staticmethod
    def _validate_entry(P, S):
        '''Validate that entry is numeric'''
        if S in '0123456789.':  # True for "" (i.e., clearing field)
            try:
                float(P)
                return True
            except ValueError:
                if P == "":  # needed to clear field
                    return True
                else:
                    return False
        else:
            return False

    def show(self):
        # self.update()
        self.geometry(self.mainframe.root.geometry())
        self.deiconify()

    def hide(self):
        self.withdraw()

    def _close(self):
        self.hide()
        self.mainframe.show()

    _validate_method = functools.partial(validate, konstants.app_methods)

#==============================================================================
# Spawn a TCL interpreter and set top window properties
#==============================================================================
root = tk.Tk()
root.title('Appendix K')
root.geometry("500x400")
center_top_level(root)

#==============================================================================
# Create a "scrollable window" when elements exceed window size
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
frame.bind("<Configure>", lambda event, canvas=canvas: onFrameConfigure(canvas))

vsb = ttk.Scrollbar(root, orient="vertical", command=canvas.yview)
vsb.pack(side="right", fill="y")

canvas.configure(yscrollcommand=vsb.set)
canvas.pack(side="left", fill="both", expand=True)
canvas.create_window((4, 4), window=frame, anchor='nw')

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
