from nfaState import NFAState

class NFA:
    def __init__(self, start_state, final_state):
        self.start_state = start_state
        self.final_state = final_state

    def matches(self, string):
        current_states = self._epsilon_closure({self.start_state})
        for char in string:
            next_states = set()
            for state in current_states:
                if char in state.transitions:
                    next_states.update(state.transitions[char])
                if '.' in state.transitions:  # Wildcard matches any character
                    next_states.update(state.transitions['.'])
            current_states = self._epsilon_closure(next_states)  # Apply epsilon closure after transition

        # Ensure that a final state is reached, and no more input remains
        return "True" if any(state.is_final for state in current_states) else "False"


    def _epsilon_closure(self, states):
        """Finds the set of states reachable via epsilon transitions."""
        stack = list(states)
        closure = set(states)
        while stack:
            state = stack.pop()
            for next_state in state.epsilon_transitions:
                if next_state not in closure:
                    closure.add(next_state)
                    stack.append(next_state)
        return closure
    