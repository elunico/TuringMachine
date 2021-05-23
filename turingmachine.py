import json
import argparse
import os.path


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-p', '--program',  default='program.json', help='path to json file containing the program object. Must contain the states object list and transition object list')
    ap.add_argument('-t', '--tape', default='tape.json', help='path to json file containing the list of tape values')
    ap.add_argument('-i', '--infinite', action='store_true', help='If the -i flag is passed, no EOT errors will be raised and tape will act as though it were infinite (until memory exhausts)')
    ap.add_argument('-q', '--quiet', action='store_true', help='Do not print each state as the machine transitions through them')
    ap.add_argument('-e', '--ensuretransitions', action='store_true', help='Ensure all possible transitions between'
                    'states are covered and raise an exception if not. Might not do what you expect. '
                    'Read the documentation for the TuringMachine#ensure_transitions() method')
    options = ap.parse_args()
    if not os.path.exists(options.program):
        ap.error('Could not find program.json. Use -p to pass the path to a json file with program object')
    if not os.path.exists(options.tape):
        ap.error('Could not find tape.json. Use -t to pass the path to a json file with tape values')
    return options


class NextAfterHalt(StopIteration):
    pass


class NoSuchTransitionRule(KeyError):
    def __init__(self, state, tapeValue) -> None:
        self.state = state
        self.tapeValue = tapeValue

    def __str__(self) -> str:
        return 'No known transition for machine in state {} with tape value of {}'.format(self.state, self.tapeValue)

    def __repr__(self) -> str:
        return 'NoSuchTransitionRule: {}'.format(str(self))


class EndOfTapeError(EOFError):
    def __init__(self, message, state, tape, index) -> None:
        self.message = message
        self.state = state
        self.tape = tape
        self.index = index

    def __str__(self) -> str:
        return '{}: state={} (tape={}) '.format(self.message, repr(self.state['name']), repr(self.tape[self.index]))

    def __repr__(self) -> str:
        return 'EndOfTapeError: {}'.format(str(self))


class TuringMachine:
    def __init__(self, states, transitions, tape) -> None:
        # data
        self.states = states
        self.transitions = transitions
        self.transition_map = {(i['startState'], i['tapeValue']): i for i in transitions}
        self.states_name = {i['name']: i for i in states}
        self.tape = tape

        # state variables
        self.state = None
        self.tapeIndex = -1
        self.errorOnEOT = True
        self.halted = False

    def initialize(self, startState, startIndex, errorOnEOT=True, verbose=True):
        '''
        Set up the Turing machine in a specific state and at a specific position
        along the tape so that it can be run beginning at this place and state

        errorOnEOT: determines whether the Turing machine will error
        if it runs out of tape or if it will append additional values to the tape as needed
        Tape is assumed to be blank if out of range.
        Default value is to error on tape end
        '''
        self.state = self.states_name[startState]
        self.tapeIndex = startIndex
        self.halted = False
        self.errorOnEOT = errorOnEOT
        self.verbose = verbose

    def run(self):
        '''Run continuously until halt or interrupt'''
        try:
            while not self.halted:
                self.next()
        except KeyboardInterrupt:
            print("Turing Machine stopped")
            self.print_state()
            return
        except NextAfterHalt:
            print("Turning Machine is halted")
            self.print_state()
            return

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
            oldTapeValue = '#'
        elif self.tapeIndex >= len(self.tape) and not self.errorOnEOT:
            self.tape.append(' ')
            oldTapeValue = '#'
        else:
            oldTapeValue = self.tape[self.tapeIndex]

        try:
            transition = self.transition_map[(self.state['name'], self.tape[self.tapeIndex])]
        except KeyError as e:
            raise NoSuchTransitionRule(repr(self.state['name']), repr(self.tape[self.tapeIndex])) from e
        nextState = transition['endState']
        valueToWrite = transition['newTapeValue']
        self.tape[self.tapeIndex] = valueToWrite
        self.state = self.states_name[nextState]
        action = transition['action']
        if action == 'left':
            self.tapeIndex -= 1
        elif action == 'right':
            self.tapeIndex += 1
        elif action.lower() == 'halt':
            self.halted = True

        stateString = "Current state {} (tape={})".format(self.state['name'], repr(oldTapeValue))
        nextString = ' | Transitioning: {} ➞ {} (tape: {} ➞ {}) then {}'.format(transition['startState'], nextState, repr(oldTapeValue), repr(valueToWrite), action)
        if self.verbose:
            print(stateString + ' ' + nextString)

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
        print('At: {} (tape={})'.format(self.tapeIndex, self.tape[self.tapeIndex]))
        print(self.tape)

    def print_tape_trimmed(self):
        trimmed = [i for i in ''.join(self.tape).strip()]
        print(repr(''.join(trimmed)))

# states.json
# a list of json objects that represent states
# states require a name


# transitions.json
# a list of json objects that represent states
# object schema should be
# {startState: ID, endState: ID, tapeValue: N, newTapeValue: N, action: A}
# where ID is the name given to the state in the object in states.json
# and where N is "0", " ", or "1" and A is left, right, stay or HALT

# tape.json
# a list of tape values in the form ["1", "0", "1", " ", " "] etc.
# when beginning a Turing machine simulation, a start index on the tape
# can be provided to simulate infinite left and right tapes
# the index is 0 based.

def main():
    options = parse_args()

    with open(options.program) as f:
        program = json.load(f)

    states = [{"name": i} for i in program['states']]
    transitions = program['transitions']
    initIndex = int(program['initialIndex'])
    initStateName = program['initialState']

    with open(options.tape) as f:
        tape = json.load(f)

    machine = TuringMachine(states, transitions, tape)
    if options.ensuretransitions:
        machine.ensure_transitions()
    machine.initialize(initStateName, initIndex, errorOnEOT=not options.infinite, verbose=not options.quiet)
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
