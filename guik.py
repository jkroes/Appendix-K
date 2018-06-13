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
import konstants
import settings
import appk
import json


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


def make_help_label(self, row, msg, photo):
    def show_help(event, msg):
        messagebox.showinfo('Help', msg)
        
    l = ttk.Label(self, image=photo)
    l.grid(row=row, column=3, sticky='W')
    l.bind('<Button-1>', functools.partial(show_help, msg=msg))
    return l


def readDetailsFromFile():
    pass


def writeDetailsToFile():
    pass

def toggle_mod_msg():
    settings.show_mod_msg = not settings.show_mod_msg


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
    texts = ['Application block size (acres):',
             'Product application rate (lbs/acre):',
             'Percent active ingredient:',
             'Application method:']
        
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
        validate_county = functools.partial(validate, self.counties)
        vcmd = (self.register(validate_county), '%P')
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
            base_path = os.getcwd()
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
        self.movable = [self.adder, self.remover, self.submitter]

        # Other instance variables
        self.root = self.winfo_toplevel()
        self.applications = []
        self.details = []

    def hide(self):
        self.root.withdraw()

    def show(self):
        # self.root.update()
        self.root.deiconify()
    
    def add_button(self):
        '''Add button for an application, provided details have been added'''
        if self.applications:
           if not self._verify_details():
               return
           if not self._verify_all_details():
               return
           
        app_number = len(self.applications) + 1
        text = 'Application {} Details'.format(app_number)
        idx = len(self.applications)
        button = ttk.Button(
            self, text=text, command=lambda idx=idx: self._add_details(idx))
        self.applications.append(button)
        
        button.details_labels = [ttk.Label(self, text=t) for t in self.texts]
        button.details = [ttk.Label(self, text='') for t in self.texts]

        button_row = len(self.movable) + (idx * (len(self.texts) + 1))
        button.grid(row=button_row, column=2, sticky='WE')
        for i, dl in enumerate(button.details_labels):
            dl.grid(row=button_row + i + 1, column=2, sticky='W')
            button.details[i].grid(
                row=button_row + i + 1, column=3, sticky='W')
            
        self._adjust_buttons(button_row)

    def rm_button(self):
        '''Remove newest app button and associated widgets, if multiple
        buttons exist'''
        idx = len(self.applications)
        if idx > 1:
            button = self.applications[-1]
            for i, dl in enumerate(button.details_labels):
                dl.destroy()
                button.details[i].destroy()
            if len(self.details) == len(self.applications):
                x = self.details.pop()
                x.destroy()
            x = self.applications.pop()
            x.destroy()
            button_row = \
                len(self.movable) + ((idx - 2) * (len(self.texts) + 1))
            self._adjust_buttons(button_row)

    def _adjust_buttons(self, row):
        '''Adjust other buttons to accommodate new/rm application button'''
        self.adder.grid(row=row, column=0)
        self.remover.grid(row=row, column=1)
        offset = row + len(self.texts) + 1
        self.submitter.grid(row=offset, column=2, sticky='WE',
            pady=25)  # Add space between rows. (padx shirnks widget width.)
        if not hasattr(self, 'submitter_help'):  # The only help button that
            self.submitter_help = make_help_label(  # moves around
                self, row=offset, msg=konstants.app_msg, photo=self.photo)
        else:
            self.submitter_help.grid(row=offset, column=3, sticky='W')

    def _add_details(self, idx):
        '''Open window to input application-specific parameters'''
        self.hide()
        if not self.details[idx:idx + 1]:
            app_number = idx + 1
            self.details.append(Details(self, app_number))
            # NOTE: Instantiation will show window automatically
        else:
            self.details[idx].show()

    def _run(self):
        '''Run command line script (appk.py) for buffer zone calculation

        NOTE: tkinter.Entry.get is the method used by all widgets
        NOTE: argparse.ArgumentParser.parse_args requires a flat list
        '''
        recalc = True if self.var.get() else False
        county = self._verify_county()
        app_details = self._verify_all_details()
        if not self._verify_details() or not app_details or not county:
            return 
        
        # Pass args to appk.py and collect results
        with contextlib.suppress(SystemExit), Capturing() as out:
            tif, other, tif_nums, other_nums =\
                appk.main(recalc, county, app_details)

        # Display "error" messages
        out = ''.join(out)
        if out:  # Display error messages from appk.py
            self._prompt(out)
            return

        # Display results
        if recalc and other:  
            if settings.show_mod_msg:
                self._show_results(konstants.mod_msg)
            other_nums = [', '.join(str(o) for o in other_nums)]
        prefix = 'TIF Applications\n\n'
        prefix2 = 'Non-TIF and Untarped Applications\n\n'
        results = self._construct_results(tif, tif_nums, prefix)
        results = self._construct_results(other, other_nums, prefix2, results) 
        self._show_results(results)

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
    
    def _verify_all_details(self):
        '''Verify that each application with a details window has all 
        details and prepare inputs for appk.py'''
        warning = ('Some applications are missing necessary '
                   'details. Please fill out all of the fields '
                   'listed in each application window.')
        warning2 = ('Ensure that the application method for each '
                   'application is fully typed out or else is '
                   'selected from the dropdown.')
        app_args = [[tk.Entry.get(i) for i in d.app_details]
            for d in self.details]     
        for app_arg in app_args:
            if not all(app_arg):
                self._prompt(warning)
                return False
            if app_arg[-1] not in konstants.app_methods:
                self._prompt(warning2)
                return False
        # Convert numeric-string inputs to floating point numbers
        for app in app_args:
            app[:-1] = [float(arg) for arg in app[:-1]]
        applications = [dict(zip(konstants.keys, values)) 
            for values in app_args]          
        return applications
        
    def _verify_details(self):
        '''Verify each application is associated with a details window'''
        warning = ('There are applications for which details have not '
                   'been added. Please add details for each application '
                   'or remove unnecessary applications.')
        if len(self.applications) != len(self.details):
            self._prompt(warning)
            return False
        return True

    def _construct_results(self, apps, apps_nums, prefix, results=''):
        template = ('Application {}:\n'
                    'Buffer zone distance: {} feet\n'
                    '(Calculated using {}.)\n\n')
        results += prefix
        if not apps:
            results += 'Not Applicable\n\n'
        for i,app in enumerate(apps):
            method = app[1]['app_method']
            result = app[0]
            results += template.format(apps_nums[i], 
                                       result,
                                       self._tbl_num(method)) 
        return results
        
    def _tbl_num(self, method):
        '''Return table used to determine buffer, 
        as listed in Appendix K'''
        county = self.county.get()
        files = (konstants.coastal_csv if county in konstants.coastal
            else konstants.inland_csv)
        file = files[konstants.app_methods[1:].index(method)]
        return file.split('.')[0]
    
    @staticmethod
    def _show_results(results):
        messagebox.showinfo('Buffer Zone Determination', results)

class Details(tk.Toplevel):
    '''Window for filling in application details'''

    def __init__(self, mainframe, app_number):
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
            
        # Configure window properties
        if sys.platform == 'darwin':  # http://wiki.tcl.tk/44444
            tk.Toplevel.__init__(self, background='#e6e6e6')
        else:
            tk.Toplevel.__init__(self)
        self.mainframe = mainframe
        self.geometry(mainframe.root.geometry())
        self.title('Appendix K - Application {} Details'.format(app_number))
        self.app_number = app_number

        # Create and position label widgets
        texts = ['Application block size (acres):',
                'Product application rate (lbs/acre):',
                'Percent active ingredient:',
                'Application method:']
        for i, t in enumerate(texts):
            ttk.Label(self, text=t).grid(row=i, column=0, sticky='W')

        # Create entry widgets
        vcmd = (self.register(validate_entry), '%P')
        entries = [ttk.Entry(self, validate='key', validatecommand=vcmd)
                        for _ in range(3)]        

        # Create combobox widget
        validate_app_method = functools.partial(validate, 
                                                konstants.app_methods)
        vcmd_meth = (self.register(validate_app_method), '%P')
        app_method = ttk.Combobox(self,
                                  width=40,
                                  values=konstants.app_methods,
                                  validate='key',
                                  validatecommand=vcmd_meth)

        # Position entry and combobox widgets
        self.app_details = entries + [app_method]
        for i in range(len(self.app_details)):
            self.app_details[i].grid(row=i, column=1, sticky='WE')

        # Create and position help labels
        msgs = [konstants.block_size_msg, konstants.rate_msg,
                konstants.percent_active_msg, konstants.method_msg]
        for i in range(4):
            make_help_label(self, row=i, msg=msgs[i],
                photo=self.mainframe.photo)

        # Create and position window navigation button
        ttk.Button(self, text='Save and Return to main screen', command=self._close
                   ).grid(row=4, column=1, pady=20)

    def show(self):
        # self.update()
        self.geometry(self.mainframe.root.geometry())
        self.deiconify()

    def hide(self):
        '''Update mainframe labels with input details and hide window'''
        idx = self.app_number - 1
        button = self.mainframe.applications[idx]
        for i, d in enumerate(button.details):
            d.configure(text=self.app_details[i].get()) 

        self.withdraw()

    def _close(self):
        self.hide()
        self.mainframe.show()
        

#==============================================================================
# Spawn a TCL interpreter and set top window properties
#==============================================================================
root = tk.Tk()
root.title('Appendix K')
root.geometry("600x400")
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
