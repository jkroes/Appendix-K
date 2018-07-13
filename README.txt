See 'tests' text file for examples of how to run this script.

Notes about script assumptions and use:
1. Script assumes that it is being run with the current directory
set to its parent directory. Additionally, the script loads
tables from a 'Tables' directory within the script's parent 
directory. 
2. Script assumes all applications listed at the command line
occur within the same county.
3. Script assumes that application block's acreage is based on a
square shape. User must normalize field shape to a square, then
input the acreage of that square.
4. Users must determine whether application block buffer zones
overlap based on script results, then recalculate sets of buffer
zones that overlap using the '--recalc' option.
5. Script does not currently consider methyl bromide buffer 
zones. 
6. Users must enter numerical inputs with the units listed
for each script argument. (See 'python appendix_k.py -h'.)
7. User must calculate broadcast-equivalent application rate
from pesticide product label. 

Known bugs:
Maximizing windows causes a bug (in the geometry method of tkinter's widgets) to manifest
when switching between the main window and application windows. The second window will not
be aligned with the previously maximized window, and switching again will use whatever size
and position the second window has at the time of the second switch.