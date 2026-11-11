"""Save and restore the address book with pickle.

pickle writes the complete AddressBook object, not only the contacts
dictionary. Loading a pickle can execute code that was stored in the file,
so addressbook.pkl must come from a trusted source.
"""

import pickle

from address_book import AddressBook


DEFAULT_FILENAME = "addressbook.pkl"

_CORRUPT_PICKLE_ERRORS = (
    pickle.UnpicklingError,
    EOFError,
    UnicodeDecodeError,
    AttributeError,
    ModuleNotFoundError,
)


class StorageError(Exception):
    """The storage file exists, but it cannot be restored as an AddressBook."""


def save_data(book: AddressBook, filename: str = DEFAULT_FILENAME) -> None:
    """Serialize the complete AddressBook to a pickle file.

    The file is opened in binary write mode. Every contact, phone number,
    and birthday stored on the object is written.
    """
    if not isinstance(book, AddressBook):
        raise TypeError("book must be an AddressBook instance")

    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename: str = DEFAULT_FILENAME) -> AddressBook:
    """Deserialize an AddressBook from a pickle file.

    Returns a new empty AddressBook when the file does not exist.
    Raises StorageError when the file is empty, corrupted, incompatible,
    or contains a different kind of object. Permission errors and other
    unexpected failures are not replaced with an empty book.
    """
    try:
        with open(filename, "rb") as file:
            book = pickle.load(file)
    except FileNotFoundError:
        return AddressBook()
    except _CORRUPT_PICKLE_ERRORS as error:
        raise StorageError(
            f"Cannot load the address book from {filename}: "
            "the file is corrupted or incompatible."
        ) from error

    if not isinstance(book, AddressBook):
        raise StorageError(
            f"Cannot load the address book from {filename}: "
            "the file does not contain an AddressBook."
        )

    return book
