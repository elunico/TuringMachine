import dataclasses
import enum
import json
from typing import Tuple, TypedDict, List, Dict, Union, TextIO


def describe(cls):
    def __str__(self):
        return '{}[{}]'.format(self.__class__.__name__,
                               ', '.join(map(lambda k: '{}={}'.format(k[0], repr(k[1])), self.__dict__.items())))

    setattr(cls, '__str__', __str__)
    setattr(cls, '__repr__', __str__)
    return cls


def dataclass(cls):
    cls = dataclasses.dataclass(cls, init=True, repr=True, eq=True, frozen=True)
    cls = describe(cls)
    return cls


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


@describe
class State:
    registry = {}

    @classmethod
    def get(cls, name: str):
        if name not in cls.registry:
            cls.registry[name] = cls(name)
        return cls.registry[name]

    def __init__(self, name: str):
        """Do not call __init__ call State.get"""
        self.name: str = name


@describe
class Transition:
    @classmethod
    def fromjson(cls, json_object: TransitionJSONObject):
        return cls(State.get(json_object['startState']), State.get(json_object['endState']), json_object['tapeValue'],
                   json_object['newTapeValue'], json_object['action'])

    def __init__(self, start_state: State, end_state: State, tapeValue: str, newTapeValue: str,
                 action: Action):
        self.start_state: State = start_state
        self.end_state: State = end_state
        self.tape_value: str = tapeValue
        self.new_tape_value: str = newTapeValue
        self.action: Action = action

    def matches(self, state: State, tape_value: str) -> bool:
        return self.start_state == state and self.tape_value == tape_value


@dataclass
class TransitionResult:
    state: State
    tape_value: str
    action: Action


@describe
class TransitionMap:
    def __init__(self, transitions: List[Transition]):
        self.transitions: List[Transition] = transitions
        self.map: Dict[Tuple[State, str], Transition] = {(i.start_state, i.tape_value): i for i in self.transitions}

    def _transition_for(self, item: Tuple[State, str]) -> Transition:
        try:
            return self.map[item]
        except KeyError as e:
            raise NoSuchTransitionRule(item[0].name, item[1])

    def understands(self, state: State, tape_value: str) -> bool:
        return (state, tape_value) in self.map

    def get_result(self, item: Tuple[State, str]) -> TransitionResult:
        transition = self._transition_for(item)
        if transition.new_tape_value == '*':
            assert item[1] == transition.tape_value
            transition.new_tape_value = transition.tape_value
        return TransitionResult(transition.end_state, transition.new_tape_value, transition.action)


class ProgramJSONObject(TypedDict):
    initialState: str
    initialIndex: int
    states: List[str]
    transitions: List[TransitionJSONObject]


@describe
class Program:
    @classmethod
    def from_file(cls, f: Union[str, TextIO]):
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
    def __init__(self, message: str, state: State, tape: List[str], index: int) -> None:
        self.message: str = message
        self.state: State = state
        self.tape: List[str] = tape
        self.index: int = index

    def __str__(self) -> str:
        return '{}: state={} (tape={}) '.format(self.message, repr(self.state.name), repr(self.tape[self.index]))

    def __repr__(self) -> str:
        return 'EndOfTapeError: {}'.format(str(self))
