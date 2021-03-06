# Turning Machine Simulation

This program (approximately) simulates a Turing machine.

It consists of several parts.

You can find the webpage for creating program JSON files [at this link](https://eluni.co/TuringMachine/web/transition-maker.html)

## importing TuringMachine
First there is a TuringMachine class which can be imported and used in other programs.
It is (fairly) well documented and hopefully self-explanatory, and type hints are used throughout,
but some time here will be dedicated to explaining it.

First you will need a program JSON object and a tape string. You can read on below
(the program.json and tape section) to learn what the schema of these objects should be.
In the event that you do not want to use a file, that is fine, as the actual object used to 
construct the TuringMachine object is a `Program` object. This class has a `from_file` method
that can load the program from JSON, or it can be constructed manually using the `__init__` method
(see source code). 

Once you construct the instance of `Program` (either programatically or 
loaded from a JSON file) you can then construct a `TuringMachine` object with the the `Program` instance and a 
string or List[str] that represented the tape (see below).
After that you can use the `next()` method
`next()` global function, iterators, or the `run()` method to run the Turing Machine simulation.
An explanation of other methods can be found below and in their documentation

If you are not interested in importing the class and just want to run a stand-alone
simulation (or if you do want to import the class but need to know the schema to use
for the program and tape) keep reading

## Running the simulations on CLI
Running the program for a simulation requires no additional libraries. It requires a
program file which contains the states of the Turing Machine, the rules for moving
between states, the initial position along the tape to start, and the initial state
to start in. In addition it requires a tape file that indicates the values on the
tape that the machine uses as I/O. See more about these files below

### Creating Files
First we will discuss the creation of the files

#### program.json
This file contains the states, transition rules, initial state, and initial tape index
that your program will use. It is a JSON file with the following schema. You can use
[this website](https://eluni.co/TuringMachine/web/transition-maker.html) to easily construct
one of these files
```json
{
  "states": [
    string...
  ],
  "transitions": [
    {"startState": string, "endState": string, "tapeValue": string, "newTapeValue": string, "action": string}...
  ],
  "initialState": string,
  "initalIndex": string,
  "tape-format": string?,
  "output-format": string?
}
```

The `"states"` key contains all the states the program will use. It is a list of strings.
These strings will be used for state names throughout the program and this list will
be considered the master list of states.

The `"transitions"` key contains a list of objects which describe transitions
between states. The `"startState"` and `"tapeValue"` keys are strings matching
state names (see above) and values of the tape (see below) and writing the
`"newTapeValue"` out to the current location, changing states, and performing the `"action"`

`"intialState"` and `"initialIndex"` describe the state to begin in and the place along the
tape (0-based) to begin at (see below)

Note that `states`, `transitions`, `initalState` and `initialIndex` are for the entire program while `startState`, `endState`, `tapeValue`, `newTapeValue`, and `action` exist inside the objects in the list of `transitions`.

`program.json` files are allowed to contain a `tape-format` key. This key is not used programmatically and
may be omitted completely, however, it can be read by a person or output by a system to indicate the
expected format of the tapes being fed into the program. The format of this string is not defined

Similarly, the `program.json` file may contain an `output-format` key. This key is optional
like `tape-format` and works in a similar way, but to explain the format of the tape upon completion,
essentially describing the output of the tape

#### Detailed explanation of transition object keys
**startState** - the ***name*** of the state the turing machine must be in to use this rule. For instance a startState of "A" means this rule applies only if the machine is in the state "A" (but not always as transition rules also consider the value on the tape
[see below])

**tapeValue** - this is the value of the tape that must be **read** to apply this rule. This value together with the `startState` key determine whether a rule is applied. Only if **the startState matches the current state *and* the current tape value matches tapeValue** will this transition rule be applied.

**endState** - this is the ***name*** of the state that the Turing machine will be in **after** applying this rule if it fits
the needed critieria

**newTapeValue** - this is the value that will be written to the **current position** of the tape before performing the
action specified by the `action` key. You can use an asterisk '*' to indicate the tape value should be the same as it was before, regardless of what it was.

**action** - this key tells the machine what to do after it has written the new tape value and changed states. The turing machine will either stay where it is on the tape, move left along the tape, move right along the tape, or HALT and end the simulation. (Values can be "stay", "left", "right", or "HALT"). Note that after this transition, since this is a simulation you may run out of tape (unlike a real turing machine which has infinite tape) see below for more information.

*Note that if you create a transition file that does not contain every single startState and tapeValue combination, then
there is a chance--though it is not guaranteed--that during the simulation the machine will be in a state and read a
tape value that it does not have rules for transitioning out of. This will raise a `NoSuchTransitionRule` error

#### tape
Since Turing machines have infinite tape but computers and people do not have infinite memory, the tape is a finite
string that contains part of what would be the actual tape used by the Turing machine. It can be passed in on the 
command line as a string, but will be presented in python as a list of singe-char strings. The TuringMachine class
can handle either a List[str] or a plain str type when passed in, though lists are recommended. 
Your tape can be as long your computer can handle and you can conceive of. You
will have the option, when running the machine, to being the simulation at any index you choose (indices are 0-based)
so you may choose to start in the middle of the tape. Note that there are two possible behaviors that will be taken,
in the event you "run out of tape". See below for more.

An example of this schema would be something like
```
1110101100101
```
or 
```
AABBBBCC
```

The tape can contain arbitrary symbols except for `*` and `#`

Since the tapes can get arbitrary long, you can also save the tape to a file and use the shell to your advantage. 
For example, on zsh for instance, you can have a file called `tape.txt` and then you can pass it to the 
program on the CLI as a string by using something like `python main.py -p program.json -t $(cat tape.txt)`

On something like CMD on Windows... you're on your own because I don't really like or use CMD but if you feel like using
an actual shell like bash or something you know what to do!

#### Error on EOT
Since Turing machines have infinite tape, but computers don't, there is the possibility of you running off the end
of the JSON array you placed in your tape.json file and essentially "running out of tape". There are two ways you may handle this. By default, if this happens the program will raise a `EndOfTapeError` and crash. You may, however, pass the
`-i` flag (or `--infinite`) which will append new state values to the tape as needed and assume empty values to be blanks.
This has the benefit of acting more like a real turing machine (until memory is exhausted) but can also easily cause an
infinite loop.

### Additional options

There is one more option you can pass which is `-e` for `ensure transitions`. This will check and raise an exception
if there is not a given transition for every possible state and tape value. This **may not be necessary** and there
may be plenty of combinations of states, transitions, and tape that do not cause a problem even if all cases are not covered.
However, using this method and having it succeed means there is not way to raise a missing transition error
during the normal operation of a simulation. Having this method fail does not mean any particular simulation
WILL fail but it might, but having the method succeed means no simulation can fail.

The `verbose` option will print the state and transition
rules being applied at each step. The default is to have this be true. If you set it to false the steps are not printed
