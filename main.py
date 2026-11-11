import sys

from bot import (
    add_birthday,
    add_contact,
    birthdays,
    change_contact,
    hello,
    parse_input,
    show_all,
    show_birthday,
    show_phone,
)
from storage import StorageError, load_data, save_data


def main() -> None:
    """Run the assistant and save the address book when the session ends."""
    try:
        book = load_data()
    except StorageError as error:
        print(error)
        sys.exit(1)

    print("Welcome to the assistant bot!")

    try:
        while True:
            user_input = input("Enter a command: ")
            command, args = parse_input(user_input)

            if command in ("close", "exit"):
                print("Good bye!")
                break

            elif command == "hello":
                print(hello())

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(book))

            else:
                print("Invalid command.")
    finally:
        save_data(book)


if __name__ == "__main__":
    main()
