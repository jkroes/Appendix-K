# Copyright

This software is Copyright (c) 2018, California Department of Pesticide 
Regulation, All rights reserved.

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

All original source code for this software is licensed under the BSD 3-Clause
License in LICENSE.txt. Software/source code used to create this application is
credited in LICENSE-3RD-PARTY.txt, which includes verbatim copies of
third-party licenses. By using this software, you agree to abide by the terms
of this license, as well as those of any third-party software used to build
this software. In particular, use or distribution of this software must comply
with the terms of use for Microsoft Distributable code. As mentioned in
LICENSE-3RD-PARTY.txt, Python®

>is linked with and uses Microsoft Distributable Code,
>copyrighted by Microsoft Corporation. The Microsoft Distributable Code
>is embedded in each .exe, .dll and .pyd file as a result of running
>the code through a linker.
>
>If you further distribute programs that include the Microsoft
>Distributable Code, you must comply with the restrictions on
>distribution specified by Microsoft. In particular, you must require
>distributors and external end users to agree to terms that protect the
>Microsoft Distributable Code at least as much as Microsoft's own
>requirements for the Distributable Code. See Microsoft's documentation
>(included in its developer tools and on its website at microsoft.com)
>for specific details.
>
>Redistribution of the Windows binary build of the Python interpreter
>complies with this agreement, provided that you do not:
>
>- alter any copyright, trademark or patent notice in Microsoft's
>Distributable Code;
>
>- use Microsoft's trademarks in your programs' names or in a way that
>suggests your programs come from or are endorsed by Microsoft;
>
>- distribute Microsoft's Distributable Code to run on a platform other
>than Microsoft operating systems, run-time technologies or application
>platforms; or
>
>- include Microsoft Distributable Code in malicious, deceptive or
>unlawful programs.
>
>These restrictions apply only to the Microsoft Distributable Code as
>defined above, not to Python itself or any programs running on the
>Python interpreter. The redistribution of the Python interpreter and
>libraries is governed by the Python Software License included with this
>file, or by other licenses as marked.

This software, through its use of Python, distributes Microsoft Distributable 
Code. This program complies with the terms above. Through the use and
distribution of this software, you in turn agree to comply with these same 
terms.

# Instructions

This software is distributed as an executable file that runs on Windows 7 or
later versions. If you experience any issues with the program, please send a 
message using the contact information located in the 
[Contact](#Contact) section of this document. 

1. To start the program, double-click the executable.
2. The main screen displays a number of fields. `Date of determination` is 
automatically populated, and the user must fill in the rest of these fields.
    - For example, the program requires the user to specify the county in 
    which the application(s) will take place. (If you want to calculate buffer
    zones for applications in multiple counties, you will need to run the 
    program once per county.)
3. Each field for user input is associated with a question-mark icon that can
be clicked to reveal a text box explaining the field and types of inputs
the field accepts. The first time you use this program, you should explore 
these help messages to familiarize yourself with the program's inputs and
features.
    - For example, the help message for `Overlapping applications` explains
    that this checkbox must be toggled if the boundaries of buffer zones would
    overlap within a specified time period. To determine whether this is the
    case, first calculate buffer zones for each application with the checkbox
    untoggled; manually determine whether any buffer zones overlap; and if
    there is one or more overlapping groups, recalculate the buffer zones 
    **separately for each separate group of overlapping applications** with the
    checkbox toggled. This step may need to be repeated as recalculated 
    buffer zones are usually larger than the original buffers. (See Step 9 for
    further information.)
4. Once each required field has been filled out (or in the case of overlapping
buffer zones, toggled), you may enter details for each application in the 
specified county for which you will calculate buffer zones. Underneath the
label for `Applications`, there are several buttons. The `+` button allows you
to add additional applications to the program. The `-` button removes the most
recently added application. Next to these is a button labeled 
`Application <#> details`, where `<#>` indicates the order in which the 
application was added to the program. Below the application button are labels
that list the input fields for an application. To input values for these 
fields, click an `Application <#> details` button. This will open a new window
for the application.
5. The application window has a number of fields. By default, the program
assumes that you need it to calculate the broadcast-equivalent application rate
for the application. If instead you need to input the broadcast rate directly,
click the checkbox for `Directly input broadcast-equivalent application rate`.
This will disable fields that represent variables in the calculation: 
`Strip or bed-bottom width (inches)` and 
`Center-to-center row spacing (inches)`. It will also change the
`Product application rate` field to a `Broadcast-equivalent application rate`
field. Note that both the `Product application rate` and
`Broadcast-equivalent application rate` fields require the user to input units
in an unlabeled, adjacent field. The units can be specified as either pounds or
gallons of product per treated acre. (The definition of treated acreage is 
given in the help message for both rate fields.)
6. Applications' fields require inputs in a specific format:
    - A formatted date: 
        - `Application date (yyyy-mm-dd)`
    - A decimal or integer number:
        - `Application block size (acres)`
        - `Product application rate` / `Broadcast-equivalent application rate`
        - `Strip or bed-bottom width (inches)`
        - `Center-to-center row spacing (inches)`
    - A dropdown option. (NOTE: If typed instead of chosen, typed input values 
    must match options listed on the dropdown lists):
        - `Registration number`
        - `Application method`
        - The unlabeled units field adjacent to the fields for rate.
1. Once application fields have been filled out with proper values, click the
button to `Save and return to main window.` Any values you input to the 
applications' fields will be displayed on the program's main window. From here,
you can add and remove applications as necessary, filling in the inputs for
each application.
8. Once all main-window and application fields are filled, click the button to
`Calculate buffer zones`. This will calculate buffer zones for each 
application and display the results. For more than 5 applications, the results
will be split into multiple windows and the window number displayed
at the bottom of each window. To view the next set of results, click `OK` on
the current results window. Each window lists the application number;
product name; buffer-zone distance (i.e., the "result"); and the 
Appendix-K-table number, broadcast-equivalent application rate, and application
block size used to determine the result.
9. As noted in the bullet under Step 3, calculated buffer zones around an
application may overlap. If this overlap occurs within 36 hours from the
time an earlier application is complete until the start of a later application,
the program will need to be run (with the `Overlapping applications` checkbox
on the main screen toggled) once for each distinct group of overlapping 
applications, **with only those applications specific to an overlap group 
input into the program for that group's run.** There are total acreage limits
that apply individually to groups of overlapping applications; additionally,
buffer-zone distances for non-TIF/untarped applications are determined from the
combined acreage, highest application rate, and the table of all the groups'
application-method tables that returns the highest buffer-zone distance. If
applications that do not overlap or from a different overlap group are
included, however, inaccurate buffer-zone distances may be calculated and
inaccurate acreage limits may be enforced, preventing an otherwise valid result
from being calculated and displayed to the user. 
    - Note that a single buffer-zone distance is calculated for all non-TIF or 
    untarped applications when  `Overlapping applications` is toggled.
    - Note that **overlap is cumulative and recursive.** If Application 1 overlaps
    Application 2 and Application 2 overlaps Application 3 within 36 hours, all
    applications are considered the same overlap group and are calculated 
    together (i.e., overlap is cumulative). In addition, if only Applications 1
    and 2 overlap originally, but upon recalculation Applications 2 and 3 also 
    overlap, then all applications would be recalculated together (i.e., 
    overlap is recursive.)


# Known Bugs

Maximizing windows causes a bug (in the geometry method of tkinter's widgets)
to manifest when switching between the main window and application windows. The
second window will not be aligned with the previously maximized window, and
switching again will use whatever size and position the second window has at
the time of the second switch.
