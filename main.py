
from regexParser import RegexParser

if __name__ == "__main__":
    # Get regex from user
    regex = input("Enter a regular expression: ")
    parser = RegexParser(regex)
    nfa = parser.parse()
    print(f"Parsed Regular Expression: {regex}")

    # Get test strings
    print("Enter strings to test the regex (type 'exit' to quit):")
    while True:
        test_string = input("Test string: ")
        if test_string.lower() == 'exit':
            break
        result = nfa.matches(test_string)
        print(f"'{test_string}': {result}")