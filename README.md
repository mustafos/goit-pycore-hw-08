# GoIT Python Core — Homework 08

**Address Book: Object Serialization and Persistence with Python Pickle**

![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-3776AB?logo=python&logoColor=white)
![Tests](https://img.shields.io/badge/tests-unittest-2ea44f)
![Project status](https://img.shields.io/badge/status-complete-2ea44f)

A command-line address book that keeps every contact after the program exits. On startup it restores the previous `AddressBook` from `addressbook.pkl` with Python's `pickle` module.

## Contents

- [Overview](#overview)
- [Features](#features)
- [How persistence works](#how-persistence-works)
- [Project structure](#project-structure)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Commands](#commands)
- [Example](#example)
- [Error handling](#error-handling)
- [Tests](#tests)
- [Design decisions](#design-decisions)
- [Git history](#git-history)

## Overview

The assistant stores contacts in an `AddressBook`. Each contact is a `Record` with a name, one or more phone numbers, and an optional birthday.

During a session the book lives in memory. When the session ends, `main` writes that same object to `addressbook.pkl`. The next launch reads the file and continues with the saved contacts, phones, and birthdays.

`pickle.dump` receives the `AddressBook` instance. The file therefore contains the book itself, including every nested `Record`, `Name`, `Phone`, and `Birthday`.

## Features

- Add a contact, add another phone, replace a phone, and show saved numbers.
- Require a phone number of exactly 10 digits.
- Store one birthday per contact in `DD.MM.YYYY` format.
- Show birthdays that fall today or within the next six days. A Saturday or Sunday greeting moves to the following Monday.
- Save the complete address book when the program exits.
- Restore that book on the next start.
- Start with an empty book when `addressbook.pkl` does not exist yet.
- Report a damaged pickle file and leave that file unchanged.
- Keep the command loop running when a command has a missing argument, an unknown contact, or an invalid value.

## How persistence works

Serialization writes an object as bytes. Deserialization reads those bytes and builds the object again.

`storage.py` owns both operations. The command handlers in `bot.py` never open the file.

### Saving

`save_data(book, filename="addressbook.pkl")` checks that `book` is an `AddressBook`, then writes it:

```python
with open(filename, "wb") as file:
    pickle.dump(book, file)
```

`"wb"` is binary write mode. Pickle output is not text. The `with` statement closes the file after the write. `pickle.dump` uses Python's default pickle protocol. A value that is not an `AddressBook` raises `TypeError` before the file is opened.

### Loading

`load_data(filename="addressbook.pkl")` reads the file:

```python
with open(filename, "rb") as file:
    book = pickle.load(file)
```

`"rb"` is binary read mode. After a successful load, the result must be an `AddressBook`. A file that contains another kind of object raises `StorageError`.

`FileNotFoundError` is the normal first-run case. `load_data` catches it and returns a new empty `AddressBook`. It does not create the file at that moment.

These read failures also become `StorageError`, with the original exception attached:

- `pickle.UnpicklingError`
- `EOFError` for an empty file
- `UnicodeDecodeError`
- `AttributeError`
- `ModuleNotFoundError`

Other errors, such as `PermissionError`, are not replaced with an empty book.

### Startup and exit

`main` loads the book before it reads any command. A `StorageError` is printed and the process exits with status `1`. In that case `save_data` is not called, so a damaged file is not overwritten.

When the load succeeds, the same book object is passed into every command. `close` and `exit` leave the input loop. A `finally` block then calls `save_data(book)` once:

```python
book = load_data()
try:
    while True:
        # read a command and update book
        if command in ("close", "exit"):
            print("Good bye!")
            break
finally:
    save_data(book)
```

The file is created in the current working directory under the name `addressbook.pkl`. An empty book is saved too, so the file appears after the first exit even when no contact was added.

If the user presses Ctrl+C, the `finally` block still writes the book. Python then reports `KeyboardInterrupt`. The program does not print `Good bye!` for that interruption.

Load a pickle only when it came from this program. Unpickling can execute code stored in the file.

## Project structure

```text
goit-pycore-hw-08/
├── address_book.py    # Field, Name, Phone, Birthday, Record, AddressBook
├── bot.py             # Command parsing, handlers, and input errors
├── storage.py         # save_data, load_data, and StorageError
├── main.py            # Startup, command loop, and save on exit
├── test_storage.py    # Persistence tests
├── README.md
└── .gitignore
```

| File | Responsibility |
| --- | --- |
| `address_book.py` | Contact model. `AddressBook` inherits from `UserDict`. |
| `bot.py` | Turns a line of input into a command result. |
| `storage.py` | Serializes and deserializes the complete `AddressBook`. |
| `main.py` | Loads the book, runs commands, and saves once at the end. |
| `test_storage.py` | Checks save, load, and a second application session. |
| `.gitignore` | Keeps generated files, including `*.pkl`, out of Git. |

`Field` stores one value. `Name`, `Phone`, and `Birthday` validate that value. `Record` is one contact. `AddressBook.add_record`, `find`, `delete`, and `get_upcoming_birthdays` operate on those records.

## Requirements

- Python 3.9 or newer. Type hints such as `list[str]` use that syntax.
- The standard library only. There is no `requirements.txt` and nothing to install.

The implementation was checked with Python 3.15.0.

## Installation

```bash
git clone git@github.com:mustafos/goit-pycore-hw-08.git
cd goit-pycore-hw-08
```

## Usage

```bash
python3 main.py
```

The prompt is `Enter a command:`. The program reads commands until `close` or `exit`. Run it again from the same directory to see the saved book.

The storage file is `addressbook.pkl` in the current working directory. If you start the program from another directory, the file is written there, not next to `main.py`.

## Commands

A contact name is one word because the input is split on spaces. `add`, `change`, `phone`, `add-birthday`, and `show-birthday` accept only the argument counts below. A missing or extra argument prints a usage line and does not change the book.

| Command | Syntax | Result |
| --- | --- | --- |
| `hello` | `hello` | Prints `How can I help you?` |
| `add` | `add John 1234567890` | Creates a contact, or adds a phone when the name already exists |
| `change` | `change John 1234567890 0987654321` | Replaces one saved phone number |
| `phone` | `phone John` | Prints all phone numbers for that contact, separated by `; ` |
| `all` | `all` | Prints every contact. A saved birthday is included in the line |
| `add-birthday` | `add-birthday John 07.11.1990` | Saves one birthday |
| `show-birthday` | `show-birthday John` | Prints the saved birthday |
| `birthdays` | `birthdays` | Prints greetings for the next seven days, including today |
| `close` | `close` | Prints `Good bye!`, saves the book, and exits |
| `exit` | `exit` | Prints `Good bye!`, saves the book, and exits |

An empty line or an unknown command prints `Invalid command.`

`birthdays` looks at dates from today through six days later. If that date is Saturday, the greeting moves to the next Monday. If it is Sunday, the greeting moves to Monday. February 29 is treated as February 28 in a year that is not a leap year. The moved Monday can fall after the original seven-day window.

## Example

The first session adds two contacts. `exit` saves them:

```text
Welcome to the assistant bot!
Enter a command: add John 1234567890
Contact added.
Enter a command: add John 0987654321
Phone added.
Enter a command: add-birthday John 07.11.1990
Birthday added.
Enter a command: add Anna 5555555555
Contact added.
Enter a command: exit
Good bye!
```

Start `python3 main.py` again in the same directory. The previous book is back:

```text
Welcome to the assistant bot!
Enter a command: all
Contact name: John, phones: 1234567890; 0987654321, birthday: 07.11.1990
Contact name: Anna, phones: 5555555555
Enter a command: phone John
1234567890; 0987654321
Enter a command: show-birthday John
07.11.1990
Enter a command: show-birthday Anna
No birthday saved for Anna.
Enter a command: close
Good bye!
```

If `addressbook.pkl` is missing, `all` prints `No contacts found.` The file is created when that session exits.

## Error handling

Command errors stay inside the `input_error` decorator. The loop continues.

| Situation | Message |
| --- | --- |
| Unknown contact | `Contact John not found.` |
| Wrong number of arguments for `add` | `Usage: add name phone` |
| Wrong number of arguments for `change` | `Usage: change name old_phone new_phone` |
| Wrong number of arguments for `phone` | `Usage: phone name` |
| Wrong number of arguments for `add-birthday` | `Usage: add-birthday name DD.MM.YYYY` |
| Wrong number of arguments for `show-birthday` | `Usage: show-birthday name` |
| Phone is not exactly 10 digits | `Phone number must contain exactly 10 digits` |
| Phone to replace is missing | `Phone number not found` |
| Date is not `DD.MM.YYYY`, or the calendar date is impossible | `Invalid date format. Use DD.MM.YYYY` |
| The contact already has a birthday | `Contact already has a birthday` |

A damaged `addressbook.pkl` stops startup:

```text
Cannot load the address book from addressbook.pkl: the file is corrupted or incompatible.
```

The process exit status is `1`, and the file bytes stay as they were.

## Tests

The tests use `unittest` from the standard library. They do not use pytest.

```bash
python3 -m unittest test_storage -v
```

Discovery runs the same module:

```bash
python3 -m unittest discover -v
```

`test_storage.py` contains 13 tests. They use temporary directories, so they do not read or write `addressbook.pkl` in the project directory.

The tests check:

- `save_data` writes a complete `AddressBook`, and rejects a plain dictionary.
- `load_data` restores several contacts, phone numbers, phone order, and birthdays.
- A restored object is an `AddressBook`, and `delete` and `get_upcoming_birthdays` still work.
- A missing file returns an empty `AddressBook` and does not create the file.
- Random bytes, an empty file, and a pickle of a dictionary raise `StorageError`.
- `exit` and `close` keep contacts for the next call to `main`.
- A session with no storage file starts empty and saves an empty book on exit.
- `KeyboardInterrupt` still leaves a readable book on disk.
- A corrupted file is reported, `main` exits with status `1`, and the file is not replaced.

## Design decisions

**The whole book is pickled.** Saving only the contacts dictionary would drop the `AddressBook` type. `pickle.dump` stores the instance, so loading returns an object whose methods still work.

**File access stays in `storage.py`.** `bot.py` handles commands. `main.py` decides when to load and save. The default filename is `addressbook.pkl`.

**The book is saved in one `finally` block.** `close` and `exit` do not call `save_data` themselves. One call covers a normal exit and a `KeyboardInterrupt`, without writing the file twice.

**A bad file is not replaced with an empty book.** `load_data` raises `StorageError` for a file it cannot trust. `main` exits before the `finally` block, so the damaged bytes remain for inspection.

**`*.pkl` is ignored.** `addressbook.pkl` is created at runtime and holds personal names, phone numbers, and birthdays. A pickle file should be loaded only from a trusted source, so Git does not track it. `.gitignore` ignores every `*.pkl`, not only the default filename.

`.gitignore` also excludes bytecode, virtual environments, `.env`, `.idea/`, `.vscode/`, `.DS_Store`, coverage output, and temporary files. `.pytest_cache/` is ignored for a local pytest run. This repository's tests are `unittest` tests. The application does not read a `.env` file.

The write is not atomic. If the process stops while `pickle.dump` is still writing, the file can be left incomplete. The next start then reports `StorageError` instead of opening a partial book as if it were valid.

## Git history

These are the commits currently stored in the repository, from the first commit to the latest:

| Commit | Message |
| --- | --- |
| `ca161ff` | `Initial commit` |
| `c508fb9` | `chore(project): prepare homework repository` |
| `b3413cc` | `feat(storage): implement address book serialization` |
| `4145b04` | `feat(storage): implement address book deserialization` |
| `d66b22b` | `feat(app): integrate persistent storage` |
| `8a2cc51` | `test(storage): add persistence tests` |
| `ae164b3` | `docs(readme): document persistence implementation` |
| `340ff1e` | `chore(git): update gitignore` |

`git log` is the source for this table. Later documentation edits are not listed here until they are committed.
