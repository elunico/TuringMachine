# Turning Machine Simulation

This program (approximately) simulates a Turing machine.

It consists of several parts.

## importing TuringMachine
First there is a TuringMachine class which can be imported and used in other programs.
It is (fairly) well documented and hopefully self-explanatory. If you want to use this
class, you should keep reading, because the schema it expeceted for states, transitions,
and the tape are described in the sections below.

If you are not interested in importing the class and just want to run a stand-alone
simulation (or if you do want to import the class but need to know the schema to use
for the states, transitions, and tape) keep reading

## Running the simulations on CLI
Running the program for a simulation requires no additional libraries. It only requires
you to do 5 things. Create 3 files and decide on 2 initial conditions.

### Creating Files
First we will discuss the creation of the files

#### states.json
First you must create a JSON file with the states that your machine will have. The JSON
file is a list of objects and each object must have a "name" key. You should be careful
at this step because the states in this file are considered the master list of states.
Any reference to the states will be done by **the names provided in this file** and it is
*case sensitive*. You will need to know these names for the next file as well so make them work

You can see some examples of state files in this repo.

#### transitions.json
Next you will need a json file that describes the transitions between states. These files
are also a list of objects. The objects must contain the keys "startState", "endState",
"tapeValue", "newTapeValue", and "action". You can use the provided website `transition-maker.html`
to create all the transitions you want and then generate a json file at the end.
The keys in the objects should be pretty self-explanatory but I will go through them

startState - the ***name*** of the state the turing machine must be in to use this rule. For instance a startState of "A" means this rule applies only if the machine is in the state "A" (but not always as transition rules also consider the value on the tape
[see below])

tapeValue - this is the value of the tape that must be **read** to apply this rule. This value together with the `startState` key determine whether a rule is applied. Only if **the startState matches the current state *and* the current tape value matches tapeValue** will this transition rule be applied (Values inlcude "1" or "0" or " ")

endState - this is the ***name*** of the state that the Turing machine will be in **after** applying this rule if it fits
the needed critieria

newTapeValue - this is the value that will be written to the **current position** of the tape before performing the
action specified by the `action` key (Values inlcude "1" or "0" or " ")

action - this key tells the machine what to do after it has written the new tape value and changed states. The turing machine will either stay where it is on the tape, move left along the tape, move right along the tape, or HALT and end the simulation. (Values can be "stay", "left", "right", or "HALT"). Note that after this transition, since this is a simulation you may run out of tape (unlike a real turing machine which has infinite tape) see below for more information.

*Note that if you create a transition file that does not contain every single startState and tapeValue combination, then
there is a chance--though it is not guaranteed--that during the simulation the machine will be in a state and read a
tape value that it does not have rules for transitioning out of. This will raise a `NoSuchTransitionRule` error

#### tape.json
Since Turing machines have infinite tape but computers and people do not have infinite memory, the tape JSON file
contains a part of the tape that the machine will use. It is a JSON file with a list of String values take from the set
{"1", "0", " "}. Your tape JSON file can be as long your computer can handle and you can conceive of. You
will have the option, when running the machine, to being the simulation at any index you choose (indices are 0-based)
so you may choose to start in the middle of the tape. Note that there are two possible behaviors that will be taken, in the event you "run out of tape". See below for more

### Command Line Args
Aside from the 3 files you must decide on 2 initial conditions and you may choose to add 1 additional 1

#### Starting State
The first thing you will need to decide is the beginning state of the simulation. You pass the ***name** (from states.json)
of this state with the `-b` flag into the program. By default the program will try and start in state "A" but if you
do not want this or don't have a state A you will need to change it

#### Starting index
You also need to choose where along your tape the machine will start. Pass the 0-based index of the place you want
to start in the array that you created in your tape.json file. By default we will start at 0 but you can (and probably shoud)
change this to whatever you like

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
