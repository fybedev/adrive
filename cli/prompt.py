def prompt_yes_no(question: str) -> bool:
    """Prompt the user with a yes/no question and return True for 'yes' and False for 'no'."""
    while True:
        response = input(f"{question} (y/n): ").strip().lower()
        if response in ('y', 'yes'):
            return True
        elif response in ('n', 'no'):
            return False
        else:
            print("Invalid input. Please enter 'y' or 'n'.")