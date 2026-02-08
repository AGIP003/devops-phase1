# Phase 2 Learning Checklist

## Features I need:
Disk Usage - HOW? - DONE
Network stats - HOW?
Color output - HOW?
Save to file - HOW?
Refresh interval - HOW?
Argparse
saves a JSON Snapshot to file
Logging


## Argparse 101
1. Import argparse

2. Create a Parser i.e parser = ....
    Parameters:
        -prog- name of the program (default=sys.argv[0])
        -usage- string describes the program usage(default: generated from arguments added to the parser)
        -description- text to display before the argument help(default: none)
        -epilog- text to display after the argument help (default: none)
        -parents- list of ArgumentParser objects whose arguments should also be included
        -formatter_class- class for customizing the help output
        -prefix_chars- set of characters that prefix optional arguments (default: ‘-‘)
        -fromfile_prefix_chars- set of characters that prefix files from which additional arguments should be read (default: None)
        -argument_default- global default value for arguments (default: None)
        -conflict_handler- strategy for resolving conflicting optionals (usually unnecessary)
        -add_help- Add a -h/--help option to the parser (default: True)
        -allow_abbrev- Allows long options to be abbreviated if the abbreviation is unambiguous. (default: True)

3. Add Arguments- info abt the arguments of the program
        -name or flags- either a name or list of option string
        -action- basic type of action to be taken when this argument is encountered at the command line
        -nargs- number of command-line arguments that should be consumed
        -const- constant value required by some action and nargs selections
        -default- value produced if the arguments are absent from the command line
        -type- type to which the command line arguments should be converted.
        -choices - A container of the allowable values for the argument 
        -required - Whether or not the command-line option may be omitted (optionals only)
        -help- brief description of what the argument does
        -metavar - A name for the argument in usage messages
        -dest - The name of the attribute to be added to the object returned by parse_args()
        
4. Parse Arguments        
5. Use Parsed Arguments
6. action ="store_true" - means it becomes a boolean flag
   - a boolean is not a file path
   - for a file path we use type=str

