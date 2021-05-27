import enum
import json
from typing import Tuple, TypedDict, List, Dict, Union, TextIO, Any, Set

from decorators import *


def check_state(method_name: str, param_name: str, value: Any):
    if not isinstance(value, State):
        raise TypeError(
            '{} method requires parameter {} to be type State not {}'.format(method_name, param_name, type(value)))


class Action(enum.Enum):
    left = 'left'
    right = 'right'
    stay = 'stay'
    HALT = 'HALT'


class TransitionJSONObject(TypedDict):
    startState: str
    endState: str
    tapeValue: str
    newTapeValue: str
    action: Action


@stringable
@hashable
class State:
    registry = {}

    _init_token = object()

    @classmethod
    def get(cls, name: str) -> 'State':
        if name not in cls.registry:
            cls.registry[name] = cls(name, State._init_token)
        return cls.registry[name]

    def __init__(self, name: str, key: object = object()) -> None:
        """Do not call __init__ call State.get"""
        if key != State._init_token:
            raise IllegalAccess('Do not call State(). Use State.get(name) to create/retrieve State objects')
        self.name: str = name


@stringable
class Transition:
    @classmethod
    def fromjson(cls, json_object: TransitionJSONObject):
        return cls(State.get(json_object['startState']), State.get(json_object['endState']), json_object['tapeValue'],
                   json_object['newTapeValue'], json_object['action'])

    def __init__(self, start_state: State, end_state: State, tapeValue: str, newTapeValue: str,
                 action: Action):
        check_state('Transition()', 'start_state', start_state)
        check_state('Transition()', 'end_state', end_state)
        self.start_state: State = start_state
        self.end_state: State = end_state
        self.tape_value: str = tapeValue
        self.new_tape_value: str = newTapeValue
        self.action: Action = action

    def matches(self, state: State, tape_value: str) -> bool:
        check_state('matches()', 'state', state)
        return self.start_state == state and self.tape_value == tape_value

    def get_result(self) -> 'TransitionResult':
        return TransitionResult(self.end_state, self.new_tape_value, self.action)


@dataclass
class TransitionResult:
    state: State
    tape_value: str
    action: Action


@stringable
class TransitionMap:
    def __init__(self, transitions: List[Transition]):
        self.transitions: List[Transition] = transitions
        self.map: Dict[Tuple[State, str], Transition] = {(i.start_state, i.tape_value): i for i in self.transitions}

    def _transition_for(self, state: State, tape_value: str) -> Transition:
        item = (state, tape_value)
        try:
            return self.map[item]
        except KeyError as e:
            raise NoSuchTransitionRule(item[0], item[1]) from None

    def understands(self, state: State, tape_value: str) -> bool:
        check_state('understands()', 'state', state)
        return (state, tape_value) in self.map

    def get_result(self, state: State, tape_value: str) -> TransitionResult:
        check_state('get_result()', 'state', state)
        transition = self._transition_for(state, tape_value)
        if transition.new_tape_value == '*':
            assert tape_value == transition.tape_value
            transition.new_tape_value = transition.tape_value
        return TransitionResult(transition.end_state, transition.new_tape_value, transition.action)


class ProgramJSONObject(TypedDict):
    initialState: str
    initialIndex: int
    states: List[str]
    transitions: List[TransitionJSONObject]


@stringable
@hashable
class TapeValues:
    def __init__(self, start_values: Set[str] = set(), written_values: Set[str] = set(), all: Set[str] = set()):
        self.start_values: Set[str] = set(start_values)
        self.written_values: Set[str] = set(written_values)
        self.all: Set[str] = set(all)


@stringable
class Program:
    @classmethod
    def from_file(cls, f: Union[str, TextIO]) -> 'Program':
        if isinstance(f, str):
            file = open(f)
        else:
            file = f

        with file as reader:
            p: ProgramJSONObject = json.load(reader)
        return Program([State.get(i) for i in p['states']], [Transition.fromjson(i) for i in p['transitions']],
                       p['initialState'], int(p['initialIndex']))

    def __init__(self, states: List[State], transitions: List[Transition], initial_state: str, initial_index: int):
        self.states = states
        self.transitions = transitions
        self.initial_state = initial_state
        self.initial_index = initial_index

    @property
    def known_tape_values(self) -> TapeValues:
        values = TapeValues()
        for transition in self.transitions:
            values.start_values.add(transition.tape_value)
            values.written_values.add(transition.new_tape_value)
        values.all = values.start_values.union(values.written_values)
        values.start_values.discard('*')
        values.written_values.discard('*')
        values.all.remove('*')
        return values


class IllegalAccess(ValueError):
    pass


class NextAfterHalt(StopIteration):
    pass


class NoSuchTransitionRule(KeyError):
    def __init__(self, state: State, tape_value: Union[List[str], str]) -> None:
        self.state = state
        self.tape_value = tape_value

    def __str__(self) -> str:
        return 'No known transition for machine in state {} with tape value of {}'.format(repr(self.state),
                                                                                          repr(self.tape_value))

    def __repr__(self) -> str:
        return 'NoSuchTransitionRule: {}'.format(str(self))


class EndOfTapeError(EOFError):
    def __init__(self, message: str, state: State, tape: List[str], index: int) -> None:
        self.message: str = message
        self.state: State = state
        self.tape: List[str] = tape
        self.index: int = index

    def __str__(self) -> str:
        if self.index < 0 or self.index >= len(self.tape):
            return '{}: Invalid position: state={} (position={}) '.format(self.message, repr(self.state.name),
                                                                          self.index)
        else:
            return '{}: Last valid position: state={} (tape={}) '.format(self.message, repr(self.state.name),
                                                                         repr(self.tape[self.index]))

    def __repr__(self) -> str:
        return 'EndOfTapeError: {}'.format(str(self))
