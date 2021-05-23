let states = [];
let transitions = [];
let tape = [];

let stateContainer = document.getElementById('states-container');
let tapeContainer = document.getElementById('tape-container');
let transitionContainer = document.getElementById('transition-container');
let makeStateButton = document.getElementById('create-state');
let makeJsonButton = document.getElementById('make-json');


makeStateButton.onclick = function () {
  // form inputs
  let startState = document.getElementById('startState').value;
  let endState = document.getElementById('endState').value;
  // let startTape = document.getElementById('startTape').selectedOptions[0].getAttribute('data-tape');
  // let endTape = document.getElementById('endTape').selectedOptions[0].getAttribute('data-tape');
  let startTape = document.getElementById('startTape').value.trim().replace('/#/g', ' ');
  let endTape = document.getElementById('endTape').value.trim().replace('/#/g', ' ');
  let action = document.getElementById('action').selectedOptions[0].id;

  // check for needed values
  if (!startState || !endState) {
    alert('startState and endState must not be blank');
    return;
  }

  // create transition data object
  let transitionData = {
    startState: startState,
    endState: endState,
    tapeValue: startTape,
    newTapeValue: endTape,
    action: action
  }

  // save the transition object data
  transitions.push(transitionData);

  // display the created transition to the users
  let transitionNode = document.createElement('div');
  transitionNode.textContent = `Transition: ${startState} ➞ ${endState} ('${startTape}' ➞ '${endTape}') [${action}]`;

  // create and add the delete button so they can remove the transition
  let deleteButton = document.createElement('input');
  deleteButton.type = 'button';
  deleteButton.value = 'Delete State';
  deleteButton.onclick = function () {
    // delete transition data
    transitionContainer.removeChild(transitionNode);
    transitions.splice(transitions.indexOf(transitionData), 1);

    // check the list of states and remove any that are no longer used
    let needRemove = [];
    for (let state of states) {
      let found = false;
      for (let transition of transitions) {
        if (state == transition.startState || state == transition.endState) {
          found = true;
        }
      }
      if (!found) {
        needRemove.push(state);
      }
    }
    // remove the states from the list and the option list for the initial State selection
    for (let state of needRemove) {
      states.splice(states.indexOf(state), 1);
      initstate.removeChild(initstate.querySelector(`option[data-state-name=${state}]`));
    }

    // same clean up business but for tape values not state values
    needRemove = [];
    for (let t of tape) {
      let found = false;
      for (let transition of transitions) {
        if (t == transition.tapeValue || t == transition.newTapeValue) {
          found = true;
        }
      }
      if (!found) {
        needRemove.push(t);
      }
    }
    // remove the states from the list and the option list for the initial State selection
    for (let t of needRemove) {
      tape.splice(tape.indexOf(t), 1);
    }
    // update the list of states in the stateContainer on the page
    stateContainer.textContent = states.join(', ');
    tapeContainer.textContent = tape.join(', ');
  }

  // append the information nodes so the user can see the program
  transitionNode.appendChild(deleteButton);
  transitionContainer.appendChild(transitionNode);

  // If the states used have never been used before, we better put them
  // in the list of states
  if (states.indexOf(startState) < 0) {
    states.push(startState);
    let newInitOption = document.createElement('option');
    newInitOption.setAttribute('data-state-name', startState);
    newInitOption.textContent = startState;
    initstate.appendChild(newInitOption);
  }
  if (states.indexOf(endState) < 0) {
    states.push(endState);
    let newInitOption = document.createElement('option');
    newInitOption.setAttribute('data-state-name', endState);
    newInitOption.textContent = endState;
    initstate.appendChild(newInitOption);
  }

  // add tape values to list so the user can see them if not already there
  if (tape.indexOf(startTape) < 0) {
    tape.push(startTape);
  }
  if (tape.indexOf(endTape) < 0) {
    tape.push(endTape);
  }
  // update the stateContainer & tapeContainer text
  stateContainer.textContent = states.join(', ');
  tapeContainer.textContent = tape.join(', ');

};

makeJsonButton.onclick = function () {
  // schema for program JSON file
  let programData = {
    "states": [],
    "transitions": [],
    initialState: undefined,
    initialIndex: undefined
  };

  // retrieve the transition data
  for (let transitionData of transitions) {
    programData.transitions.push(transitionData);
  }

  // retrieve the list of states
  for (let state of states) {
    programData.states.push(state);
  }

  // retrieve these two items from the form
  programData.initialState = document.getElementById('initstate').selectedOptions[0].getAttribute(
    'data-state-name');
  programData.initialIndex = document.getElementById('initindex').value;

  let jsonString = JSON.stringify(programData);

  // download the json data
  downloadToFile(jsonString, 'program.json', 'application/json');
};

function downloadToFile(content, filename, contentType) {
  // from https://robkendal.co.uk/blog/2020-04-17-saving-text-to-client-side-file-using-vanilla-js
  const a = document.createElement('a');
  const file = new Blob([content], {
    type: contentType
  });

  a.href = URL.createObjectURL(file);
  a.download = filename;
  a.click();

  URL.revokeObjectURL(a.href);
};
