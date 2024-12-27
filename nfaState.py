class NFAState:
    def __init__(self, is_final=False):
        self.is_final = is_final
        self.transitions = {}  # Maps symbols to sets of states
        self.epsilon_transitions = set()  # Transitions without consuming input

    def add_transition(self, symbol, state):
        if symbol not in self.transitions:
            self.transitions[symbol] = set()
        self.transitions[symbol].add(state)

    def add_epsilon_transition(self, state):
        self.epsilon_transitions.add(state)