def yes_no_input():
    choice = input("Please respond with 'yes' or 'no' [y/N]: ").lower()
    if choice in ['y', 'ye', 'yes']:
        return True
    elif choice in ['n', 'no']:
        return False
    else:
        return False
