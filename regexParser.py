from nfaState import NFAState
from nfa import NFA

class RegexParser:
    def __init__(self, regex):
        self.regex = regex
        self.position = 0

    def parse(self):
        if self.regex[self.position] == '^':  
            self.position += 1  
        nfa = self._expression()
        if self.position < len(self.regex) and self.regex[self.position] == '$':  
            self.position += 1  
            final_state = NFAState(is_final=True)
            nfa.final_state.add_epsilon_transition(final_state)
            nfa.final_state = final_state  # Set the final state to the new one
        if self.position < len(self.regex):
            raise ValueError(f"Unexpected character at position {self.position}: {self.regex[self.position]}")
        return nfa

    def _expression(self):
        """Parses an expression (sequence of terms)."""
        term_nfa = self._term()
        if self.position < len(self.regex) and self.regex[self.position] == '|':
            self.position += 1
            next_term_nfa = self._expression()
            return self._combine_union(term_nfa, next_term_nfa)  # Combine using union for alternation
        return term_nfa

    def _term(self):
        """Parses a term (sequence of factors)."""
        factor_nfa = self._factor()
        while self.position < len(self.regex) and self.regex[self.position] not in ')|':
            next_factor_nfa = self._factor()
            factor_nfa = self._combine_concatenation(factor_nfa, next_factor_nfa)
        return factor_nfa

    def _factor(self):
        """Parses a factor (base with optional repetition)."""
        base_nfa = self._base()
        if self.position < len(self.regex):
            char = self.regex[self.position]
            if char in '*+?':
                self.position += 1
                if char == '*':
                    return self._apply_star(base_nfa)
                elif char == '+':
                    return self._apply_plus(base_nfa)  # Correctly applies '+' to the entire alternation
                elif char == '?':
                    return self._apply_question(base_nfa)
        return base_nfa


    def _base(self):
        """Parses a base (parentheses, character classes, or single characters)."""
        if self.position < len(self.regex):
            char = self.regex[self.position]
            if char == '(':
                self.position += 1
                nfa = self._expression()
                if self.position >= len(self.regex) or self.regex[self.position] != ')':
                    raise ValueError("Unmatched parentheses")
                self.position += 1
                return nfa
            elif char == '|':
                raise ValueError("Unexpected '|' outside of parentheses")
            elif char in '+*?':
                raise ValueError(f"Unexpected quantifier '{char}' without preceding expression")
            elif char == '.':
                self.position += 1
                return self._create_wildcard_nfa()
            else:
                self.position += 1
                return self._create_single_char_nfa(char)
        raise ValueError("Unexpected end of regex")


    def _combine_concatenation(self, nfa1, nfa2):
        # Add epsilon transition from nfa1's final state to nfa2's start state
        nfa1.final_state.add_epsilon_transition(nfa2.start_state)
    
        # Make the first NFA's final state non-final
        nfa1.final_state.is_final = False
    
        # Ensure the second NFA's final state is marked as final
        nfa2.final_state.is_final = True
    
        # Return the new NFA with the start state of nfa1 and final state of nfa2
        return NFA(nfa1.start_state, nfa2.final_state)

    def _combine_union(self, nfa1, nfa2):
        # Create new start and final states
        start_state = NFAState()
        final_state = NFAState(is_final=True)

        # Add epsilon transitions to the start of nfa1 and nfa2
        start_state.add_epsilon_transition(nfa1.start_state)
        start_state.add_epsilon_transition(nfa2.start_state)

        # Connect the final states of nfa1 and nfa2 to the new final state
        nfa1.final_state.add_epsilon_transition(final_state)
        nfa2.final_state.add_epsilon_transition(final_state)

        # Ensure intermediate final states are not marked as final
        nfa1.final_state.is_final = False
        nfa2.final_state.is_final = False

        # Return the combined NFA
        return NFA(start_state, final_state)


    def _create_single_char_nfa(self, char):
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        start_state.add_transition(char, final_state)
        return NFA(start_state, final_state)

    def _create_wildcard_nfa(self):
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        start_state.add_transition('.', final_state)
        return NFA(start_state, final_state)

    def _create_anchor_nfa(self, anchor):
        if anchor != '$':
            raise ValueError(f"Unsupported anchor: {anchor}")
    
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        # Add an epsilon transition to the final state, only valid if no input remains
        start_state.add_epsilon_transition(final_state)
        return NFA(start_state, final_state)


    def _parse_character_class(self):
        
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        inside_class = set()

        while self.position < len(self.regex) and self.regex[self.position] != ']':
            char = self.regex[self.position]

            if char == '-' and self.position > 0 and self.regex[self.position - 1] != '[' and self.position + 1 < len(self.regex) and self.regex[self.position + 1] != ']':
                
                start = self.regex[self.position - 1]
                end = self.regex[self.position + 1]
                if ord(start) > ord(end):
                    raise ValueError(f"Invalid range {start}-{end} in character class")
                inside_class.update(chr(c) for c in range(ord(start), ord(end) + 1))
                self.position += 1  # Skip the range's end character
            else:
                # Add individual characters to the class
                inside_class.add(char)

            self.position += 1

        if self.position >= len(self.regex) or self.regex[self.position] != ']':
            raise ValueError("Unmatched character class")
        self.position += 1

        # Create transitions for all characters in the character class
        for char in inside_class:
            start_state.add_transition(char, final_state)

        return NFA(start_state, final_state)


    def _apply_star(self, nfa):
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        start_state.add_epsilon_transition(nfa.start_state)
        start_state.add_epsilon_transition(final_state)
        nfa.final_state.add_epsilon_transition(final_state)
        nfa.final_state.add_epsilon_transition(nfa.start_state)
        nfa.final_state.is_final = False
        return NFA(start_state, final_state)

    def _apply_plus(self, nfa):
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        start_state.add_epsilon_transition(nfa.start_state)
        nfa.final_state.add_epsilon_transition(final_state)
        nfa.final_state.add_epsilon_transition(nfa.start_state)
        nfa.final_state.is_final = False
        return NFA(start_state, final_state)

    def _apply_question(self, nfa):
        start_state = NFAState()
        final_state = NFAState(is_final=True)
        start_state.add_epsilon_transition(nfa.start_state)
        start_state.add_epsilon_transition(final_state)
        nfa.final_state.add_epsilon_transition(final_state)
        nfa.final_state.is_final = False
        return NFA(start_state, final_state)

    def _apply_repetition(self, nfa):
        repeat_range = ""
        while self.position < len(self.regex) and self.regex[self.position] != '}':
            repeat_range += self.regex[self.position]
            self.position += 1

        if not repeat_range or self.position >= len(self.regex) or self.regex[self.position] != '}':
            raise ValueError("Invalid repetition syntax")
        self.position += 1  # Skip the closing '}'

        # Parse repetition range
        if ',' in repeat_range:
            parts = repeat_range.split(',')
            min_repeat = int(parts[0])
            max_repeat = int(parts[1]) if parts[1] else None
        else:
            min_repeat = max_repeat = int(repeat_range)

        # Build NFA for repetition
        start_state = NFAState()
        final_state = NFAState(is_final=True)

        current_nfa = nfa
        prev_state = start_state

        # Add exact minimum repetitions
        for _ in range(min_repeat):
            next_nfa = self._duplicate_nfa(nfa)
            prev_state.add_epsilon_transition(next_nfa.start_state)
            prev_state = next_nfa.final_state

        # Add optional repetitions up to max_repeat
        if max_repeat is not None:
            for _ in range(max_repeat - min_repeat):
                optional_nfa = self._duplicate_nfa(nfa)
                prev_state.add_epsilon_transition(optional_nfa.start_state)
                prev_state.add_epsilon_transition(final_state)
                prev_state = optional_nfa.final_state

        # Add unlimited repetitions for {x,}
        if max_repeat is None:
            loop_nfa = self._apply_star(self._duplicate_nfa(nfa))
            prev_state.add_epsilon_transition(loop_nfa.start_state)
            prev_state = loop_nfa.final_state

        prev_state.add_epsilon_transition(final_state)
        return NFA(start_state, final_state)


    def _duplicate_nfa(self, nfa):
        
        state_map = {}

        def clone_state(state):
            if state not in state_map:
                state_map[state] = NFAState(is_final=state.is_final)
            return state_map[state]

        for state in nfa.start_state.epsilon_transitions | {nfa.start_state}:
            new_state = clone_state(state)
            for symbol, targets in state.transitions.items():
                for target in targets:
                    new_state.add_transition(symbol, clone_state(target))
            for target in state.epsilon_transitions:
                new_state.add_epsilon_transition(clone_state(target))

        return NFA(clone_state(nfa.start_state), clone_state(nfa.final_state))