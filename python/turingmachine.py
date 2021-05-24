from models import TransitionResult
from typing import List, Tuple

from models import State, TransitionMap, NoSuchTransitionRule, Program, NextAfterHalt, EndOfTapeError, Action


class TuringMachine:
    def __init__(self, program: Program, tape: List[str]) -> None:
        # data
        self.states: List[State] = program.states
        self.transition_map: TransitionMap = TransitionMap(program.transitions)
        self.tape: List[str] = tape

        # state variables
        self.state: State = State.get(program.initial_state)
        self.tapeIndex: int = program.initial_index
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

    def __iter__(self) -> 'TuringMachine':
        return self

    def __next__(self) -> Tuple[State, str]:
        return self.next()

    def next(self) -> Tuple[State, str]:
        """transition to the next state and then hold"""
        if self.halted:
            raise NextAfterHalt()

        # before we continue with the next step
        # we need to fill in the tape if we ran off the end
        # or we need to raise an Exception indicating the tape ended
        old_tape_value: str = self._check_end_of_tape()

        # save the current state so that we can return it
        this_step: Tuple[State, str] = (self.state, old_tape_value)

        # now that we check for end of tape, the tape has been modified as needed so that we can
        # property respond to the next transition. old_tape_value may be '#' to indicate
        # running off the tape, but since we assume # to be ' ' we do not pass old_tape_value to
        # get_result
        result: TransitionResult = self.transition_map.get_result(self.state, self.tape[self.tapeIndex])
        self.tape[self.tapeIndex] = result.tape_value
        self.state = result.state
        self._perform_action(result.action)

        if self.verbose:
            state_string = "Current state {} (tape={})".format(self.state.name, repr(old_tape_value))
            next_string = ' | Transitioning: {} ➞ {} (tape: {} ➞ {}) then {}'.format(this_step[0],
                                                                                     result.state,
                                                                                     repr(old_tape_value),
                                                                                     repr(result.tape_value),
                                                                                     result.action.lower())
            print(state_string + ' ' + next_string)

        return this_step

    def _perform_action(self, action: Action):
        action = action.lower()
        if action == 'left':
            self.tapeIndex -= 1
        elif action == 'right':
            self.tapeIndex += 1
        elif action == 'halt':
            self.halted = True

    def _check_end_of_tape(self) -> str:
        """This method is called to determine if we have run off the end of the tape
        If we have and an error should be raised (indicated by self.errorOnEot) then
        an error is raised, otherwise the tape is modified accordingly (placing a blank
        in the new position). The return value is to indicate a real blank ' ' value
        vs a filled in value indicated by # when falling off the tape.

        :returns the value of the tape in the current step or # if we ran off the tape
        :raises EndOfTapeError if we fell off the tape and have it set to raise an error"""
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
        return old_tape_value

    def transition_for_step(self, step: Tuple[State, str]) -> TransitionResult:
        state, tape = step
        if tape == '#' and self.errorOnEOT:
            if self.tapeIndex < 0:
                raise EndOfTapeError("Fell off left side", self.state, self.tape, self.tapeIndex + 1)
            elif self.tapeIndex >= len(self.tape):
                raise EndOfTapeError("Fell off right side", self.state, self.tape, self.tapeIndex - 1)
        elif tape == '#' and not self.errorOnEOT:
            tape = ' '

        return self.transition_map.get_result(state, tape)

    def ensure_transitions(self, tape_values: Tuple[str] = ('1', '0', ' ')):
        """ensures there is a transition rule for every state with all possible tape values
        this ensures that the NoSuchTransitionRule error will never be raised while running
        to prevents run from ending due to an oversight. This method may take LONG to complete

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
        """
        print('WARNING: This TuringMachine#ensure_transitions() may not do what you think. Read the documentation')
        tape_values = list(tape_values)
        for state in self.states:
            name = state.name
            for transition in self.transition_map.transitions:
                if transition.start_state == name:
                    tape_values.remove(transition.tape_value)
            if len(tape_values) != 0:
                raise NoSuchTransitionRule(state.name, tape_values)

    def dump_tape(self):
        print('Current State: {}'.format(self.state.name))
        print('At: {} (tape={})'.format(self.tapeIndex, self.tape[self.tapeIndex]))
        print(self.tape)

    def print_tape_trimmed(self):
        trimmed = [i for i in ''.join(self.tape).strip()]
        print(repr(''.join(trimmed)))
