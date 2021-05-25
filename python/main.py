import argparse
import os
import json

from models import Program
from turingmachine import TuringMachine


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('--explain', required=False, help='Print out the "tape-format" and "output-format" keys of the given program JSON file passed to --expalin if they exist and exit')
    ap.add_argument('-p', '--program', default='program.json',
                    help='path to json file containing the program object. Must contain the states object list and transition object list')
    ap.add_argument('-t', '--tape', default='tape.json', help='path to json file containing the list of tape values')
    ap.add_argument('-i', '--infinite', action='store_true',
                    help='If the -i flag is passed, no EOT errors will be raised and tape will act as though it were infinite (until memory exhausts)')
    ap.add_argument('-q', '--quiet', action='store_true',
                    help='Do not print each state as the machine transitions through them')
    ap.add_argument('-e', '--ensuretransitions', action='store_true', help='Ensure all possible transitions between'
                                                                           'states are covered and raise an exception if not. Might not do what you expect. '
                                                                           'Read the documentation for the TuringMachine#ensure_transitions() method')
    options = ap.parse_args()
    if not options.explain:
        if not os.path.exists(options.program):
            ap.error('Could not find program.json. Use -p to pass the path to a json file with program object')
        if not os.path.exists(options.tape):
            ap.error('Could not find tape.json. Use -t to pass the path to a json file with tape values')
    return options


def main():
    options = parse_args()

    if options.explain:
        with open(options.explain) as f:
            program = json.load(f)
        print("==== \033[1mExpected tape input format:\033[0m ==== ")
        print(program.get('tape-format', '<not provided>'))
        print()
        print("==== \033[1mExpected tape output format:\033[0m ====")
        print(program.get('output-format', '<not provided>'))
        return

    with open(options.tape) as f:
        tape = json.load(f)

    program = Program.from_file(options.program)
    machine = TuringMachine(program, tape)
    if options.ensuretransitions:
        machine.ensure_transitions()
    machine.initialize(err_on_eot=not options.infinite, verbose=not options.quiet)
    print("Machine start!")
    print("Tape output (without blanks)")
    machine.print_tape_trimmed()
    if not options.quiet:
        print("\nBeginning simulation...")
    machine.run()
    print('\nFinished!')
    print("Tape output (without blanks)")
    machine.print_tape_trimmed()


if __name__ == '__main__':
    main()
