import argparse
import enum
import json
import os.path
from typing import Dict, List, TypedDict, Tuple, Union


def parse_args():
    ap = argparse.ArgumentParser()
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
    if not os.path.exists(options.program):
        ap.error('Could not find program.json. Use -p to pass the path to a json file with program object')
    if not os.path.exists(options.tape):
        ap.error('Could not find tape.json. Use -t to pass the path to a json file with tape values')
    return options


class Action(enum.Enum):
    left = 'left'
    right = 'right'
    stay = 'stay'
    HALT = 'HALT'


class TransitionObject(TypedDict):
    startState: str
    endState: str
    tapeValue: str
    newTapeValue: str
    action: Action


class StateObject(TypedDict):
    name: str


class Program(TypedDict):
    initialState: str
    initialIndex: int
    states: List[str]
    transitions: List[TransitionObject]


class NextAfterHalt(StopIteration):
    pass


class NoSuchTransitionRule(KeyError):
    def __init__(self, state: str, tape_value: Union[List[str], str]) -> None:
        self.state = state
        self.tape_value = tape_value

    def __str__(self) -> str:
        return 'No known transition for machine in state {} with tape value of {}'.format(self.state, self.tape_value)

    def __repr__(self) -> str:
        return 'NoSuchTransitionRule: {}'.format(str(self))


class EndOfTapeError(EOFError):
    def __init__(self, message: str, state: StateObject, tape: List[str], index: int) -> None:
        self.message: str = message
        self.state: StateObject = state
        self.tape: List[str] = tape
        self.index: int = index

    def __str__(self) -> str:
        return '{}: state={} (tape={}) '.format(self.message, repr(self.state['name']), repr(self.tape[self.index]))

    def __repr__(self) -> str:
        return 'EndOfTapeError: {}'.format(str(self))


class TuringMachine:
    def __init__(self, program: Program, tape: List[str]) -> None:
        # data
        self.states: List[StateObject] = [{'name': i} for i in program['states']]
        self.transitions: List[TransitionObject] = program['transitions']
        self.transition_map: Dict[Tuple[str, str], TransitionObject] = {(i['startState'], i['tapeValue']): i for i in
                                                                        self.transitions}
        self.states_name: Dict[str, StateObject] = {i['name']: i for i in self.states}
        self.tape: List[str] = tape

        # state variables
        self.state: StateObject = self.states_name[program['initialState']]
        self.tapeIndex: int = int(program['initialIndex'])
        self.errorOnEOT: bool = True
        self.halted: bool = False
        self.verbose: bool = True
        self.initialize()

    def initialize(self, err_on_eot: bool = True, verbose: bool = True):
        """
        err_on_eot: determines whether the Turing machine will error
        if it runs out of tape or if it will append additional values to the tape as needed
        Tape is assumed to be blank if out of range.
        Default value is to error on tape end
        """
        self.halted = False
        self.errorOnEOT = err_on_eot
        self.verbose = verbose

    def run(self):
        """Run continuously until halt or interrupt"""
        try:
            while not self.halted:
                self.next()
        except KeyboardInterrupt:
            print("Turing Machine stopped")
            self.dump_tape()
            return
        except NextAfterHalt:
            print("Turning Machine is halted")
            self.dump_tape()
            return

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        '''transition to the next state and then hold'''
        if self.halted:
            raise NextAfterHalt()

        # before we continue with the next step
        # we need to fill in the tape if we ran off the end
        # or we need to raise an Exception indicating the tape ended
        if self.tapeIndex < 0 and self.errorOnEOT:
            raise EndOfTapeError("Fell off left side", self.state, self.tape, self.tapeIndex + 1)
        elif self.tapeIndex >= len(self.tape) and self.errorOnEOT:
            raise EndOfTapeError("Fell off right side", self.state, self.tape, self.tapeIndex - 1)

        if self.tapeIndex < 0 and not self.errorOnEOT:
            self.tape = [' '] + self.tape
            self.tapeIndex = 0
            old_tape_value: str = '#'
        elif self.tapeIndex >= len(self.tape) and not self.errorOnEOT:
            self.tape.append(' ')
            old_tape_value: str = '#'
        else:
            old_tape_value: str = self.tape[self.tapeIndex]

        this_step: Tuple[str, str] = (self.state['name'], old_tape_value)
        try:
            transition = self.transition_map[(self.state['name'], self.tape[self.tapeIndex])]
        except KeyError as e:
            raise NoSuchTransitionRule(repr(self.state['name']), repr(self.tape[self.tapeIndex])) from e
        next_state = transition['endState']
        value_to_write = transition['newTapeValue']
        self.tape[self.tapeIndex] = value_to_write
        self.state = self.states_name[next_state]
        action: str = transition['action'].lower()
        if action == 'left':
            self.tapeIndex -= 1
        elif action == 'right':
            self.tapeIndex += 1
        elif action == 'halt':
            self.halted = True

        if self.verbose:
            state_string = "Current state {} (tape={})".format(self.state['name'], repr(old_tape_value))
            next_string = ' | Transitioning: {} ➞ {} (tape: {} ➞ {}) then {}'.format(transition['startState'],
                                                                                     next_state,
                                                                                     repr(old_tape_value),
                                                                                     repr(value_to_write), action)
            print(state_string + ' ' + next_string)

        return this_step

    def transition_for_step(self, step):
        state, tape = step
        if tape == '#' and self.errorOnEOT:
            if self.tapeIndex < 0:
                raise EndOfTapeError("Fell off left side", self.state, self.tape, self.tapeIndex + 1)
            elif self.tapeIndex >= len(self.tape):
                raise EndOfTapeError("Fell off right side", self.state, self.tape, self.tapeIndex - 1)
        elif tape == '#' and not self.errorOnEOT:
            tape = ' '

        return self.transition_map[(state, tape)]

    def ensure_transitions(self):
        '''ensures there is a transition rule for every state with all possible tape values
        this ensures that the NoSuchTransitionRule error will never be raised while running
        to preventa run from ending due to an oversight. This method may take LONG to complete

        Note that it is not always necessary to call this method. Sometimes a machine will run
        perfectly fine without a valid transition between all states. Calling this method
        and having it raise an exception does not necessarily mean that such an exception would
        be raised during normal operation of the machine on a particular tape or any tape.

        For instance a tape of only 1s and a machine with only 1 state 'A' and only 1 rule
        A -> A (1 -> 1) [stay] would run forever and never raise a missing transition rule
        error, yet this method would notice that there is no Rule for A when the tape is 0 or ' '
        and then raise an exception. This method does not simulate a run (that is what run
        is for) it can only tell you if every single transition rule is covered for all the
        states that exist regardless of whether or not they will ever be hit or are needed.
        If this method exits successfully, it is not possible to raise a NoSuchTransitionRule
        error, however if this method FAILS then it is not clear whether a particular
        run with a given tape will raise the excpetion or not.
        '''
        print('WARNING: This TuringMachine#ensure_transitions() may not do what you think. Read the documentation')
        for state in self.states:
            name = state['name']
            tapeValues = ['1', '0', ' ']
            for transition in self.transitions:
                if transition['startState'] == name:
                    tapeValues.remove(transition['tapeValue'])
            if len(tapeValues) != 0:
                raise NoSuchTransitionRule(state['name'], tapeValues)

    def dump_tape(self):
        print('Current State: {}'.format(self.state['name']))
        print('At: {} (tape={})'.format(self.tapeIndex, self.tape[self.tapeIndex]))
        print(self.tape)

    def print_tape_trimmed(self):
        trimmed = [i for i in ''.join(self.tape).strip()]
        print(repr(''.join(trimmed)))


def main():
    options = parse_args()

    with open(options.program) as f:
        program = json.load(f)

    with open(options.tape) as f:
        tape = json.load(f)

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
