import json
import argparse
import os.path


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument('-s', '--states',  default='states.json', help='path to json file containing the list of state objects')
    ap.add_argument('-t', '--transitions', default='transitions.json', help='path to json file containing the list of transition objects')
    ap.add_argument('-p', '--tape', default='tape.json', help='path to json file containing the list of tape values')
    options = ap.parse_args()
    if not os.path.exists(options.states):
        ap.error('Could not find states.json. Use -s to pass the path to a json file with state objects')
    if not os.path.exists(options.transitions):
        ap.error('Could not find transitions.json. Use -t to pass the path to a json file with transition objects')
    if not os.path.exists(options.tape):
        ap.error('Could not find tape.json. Use -p to pass the path to a json file with tape values')
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
        self.halted = False

    def initialize(self, startState, startIndex, errorOnEOT=True):
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

    def run(self, verbose=True):
        '''Run continuously until halt or interrupt'''
        try:
            while not self.halted:
                if verbose:
                    self.print_state()
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

    def print_state(self):
        print("Current state {} (tape={})".format(self.state['name'], repr(self.tape[self.tapeIndex])))


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

    with open(options.states) as f:
        states = json.load(f)

    with open(options.transitions) as f:
        transitions = json.load(f)

    with open(options.tape) as f:
        tape = json.load(f)

    machine = TuringMachine(states, transitions, tape)
    machine.initialize('A', 5)
    machine.run()


if __name__ == '__main__':
    main()
