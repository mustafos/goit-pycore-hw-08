import os
import pickle
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime
from unittest.mock import patch

from address_book import AddressBook, Birthday, Phone, Record
from main import main
from storage import StorageError, load_data, save_data


@contextmanager
def temporary_directory():
    """Change to a temporary directory, then restore the previous one."""
    previous = os.getcwd()

    with tempfile.TemporaryDirectory() as directory:
        os.chdir(directory)

        try:
            yield directory
        finally:
            os.chdir(previous)


def sample_book():
    """Build an address book with several contacts, phones, and birthdays."""
    book = AddressBook()

    john = Record("John")
    john.add_phone("1234567890")
    john.add_phone("0987654321")
    john.add_birthday("07.11.1990")
    book.add_record(john)

    anna = Record("Anna")
    anna.add_phone("5555555555")
    book.add_record(anna)

    jane = Record("Jane")
    jane.add_phone("1112223333")
    jane.add_birthday("29.02.2000")
    book.add_record(jane)

    return book


class TestSaveData(unittest.TestCase):
    def test_save_writes_the_complete_address_book(self):
        book = sample_book()

        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            save_data(book, filename)

            self.assertTrue(os.path.isfile(filename))
            self.assertGreater(os.path.getsize(filename), 0)

            with open(filename, "rb") as file:
                restored = pickle.load(file)

        self.assertIsInstance(restored, AddressBook)
        self.assertIsNot(restored, book)
        self.assertEqual(list(restored.data), ["John", "Anna", "Jane"])

    def test_save_rejects_a_plain_dictionary(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            with self.assertRaises(TypeError):
                save_data({"John": "1234567890"}, filename)

            self.assertFalse(os.path.exists(filename))


class TestLoadData(unittest.TestCase):
    def test_load_restores_an_existing_address_book(self):
        book = sample_book()

        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "contacts.pkl")
            save_data(book, filename)
            restored = load_data(filename)

        self.assertIsInstance(restored, AddressBook)
        self.assertEqual(len(restored.data), 3)
        self.assertEqual(restored.find("Anna").name.value, "Anna")

    def test_load_restores_multiple_contacts_phones_and_birthdays(self):
        book = sample_book()

        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")
            save_data(book, filename)
            restored = load_data(filename)

        john = restored.find("John")
        anna = restored.find("Anna")
        jane = restored.find("Jane")

        self.assertEqual(
            [phone.value for phone in john.phones],
            ["1234567890", "0987654321"],
        )
        self.assertTrue(all(isinstance(phone, Phone) for phone in john.phones))
        self.assertIsInstance(john.birthday, Birthday)
        self.assertEqual(john.birthday.value, datetime(1990, 11, 7))
        self.assertEqual(str(john.birthday), "07.11.1990")

        self.assertEqual(anna.phones[0].value, "5555555555")
        self.assertIsNone(anna.birthday)

        self.assertEqual(jane.phones[0].value, "1112223333")
        self.assertEqual(jane.birthday.value, datetime(2000, 2, 29))
        self.assertEqual(str(jane.birthday), "29.02.2000")

    def test_loaded_book_keeps_address_book_behavior(self):
        book = sample_book()

        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")
            save_data(book, filename)
            restored = load_data(filename)

        restored.delete("Anna")
        self.assertIsNone(restored.find("Anna"))

        class FrozenDateTime(datetime):
            @classmethod
            def today(cls):
                return cls(2026, 11, 4)

        with patch("address_book.datetime", FrozenDateTime):
            upcoming = restored.get_upcoming_birthdays()

        self.assertEqual(
            upcoming,
            [{"name": "John", "congratulation_date": "09.11.2026"}],
        )

    def test_missing_file_returns_an_empty_address_book(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "missing.pkl")

            restored = load_data(filename)

            self.assertIsInstance(restored, AddressBook)
            self.assertEqual(len(restored.data), 0)
            self.assertFalse(os.path.exists(filename))

    def test_corrupted_pickle_raises_storage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            with open(filename, "wb") as file:
                file.write(b"this is not a pickle")

            with self.assertRaises(StorageError) as error:
                load_data(filename)

            self.assertIsInstance(error.exception.__cause__, pickle.UnpicklingError)
            self.assertIn("corrupted or incompatible", str(error.exception))

            with open(filename, "rb") as file:
                self.assertEqual(file.read(), b"this is not a pickle")

    def test_empty_pickle_file_raises_storage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            with open(filename, "wb") as file:
                file.write(b"")

            with self.assertRaises(StorageError) as error:
                load_data(filename)

            self.assertIsInstance(error.exception.__cause__, EOFError)

    def test_non_address_book_pickle_raises_storage_error(self):
        with tempfile.TemporaryDirectory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            with open(filename, "wb") as file:
                pickle.dump({"John": "1234567890"}, file)

            with self.assertRaises(StorageError) as error:
                load_data(filename)

            self.assertIn("does not contain an AddressBook", str(error.exception))
            self.assertIsNone(error.exception.__cause__)


class TestApplicationPersistence(unittest.TestCase):
    def _run(self, commands, printed=None):
        commands = iter(commands)

        if printed is None:
            printed = []

        def fake_input(_prompt):
            try:
                command = next(commands)
            except StopIteration as error:
                raise AssertionError("Command loop did not exit.") from error

            if isinstance(command, BaseException):
                raise command

            return command

        with patch("builtins.input", fake_input):
            with patch(
                "builtins.print",
                lambda *args: printed.append(" ".join(map(str, args))),
            ):
                main()

        return printed

    def test_contacts_survive_exit_and_a_new_start(self):
        with temporary_directory():
            first_session = self._run(
                [
                    "add John 1234567890",
                    "add John 0987654321",
                    "add-birthday John 07.11.1990",
                    "add Anna 5555555555",
                    "exit",
                ]
            )

            self.assertIn("Contact added.", first_session)
            self.assertIn("Phone added.", first_session)
            self.assertIn("Birthday added.", first_session)
            self.assertEqual(first_session[-1], "Good bye!")
            self.assertTrue(os.path.isfile("addressbook.pkl"))

            second_session = self._run(
                [
                    "all",
                    "phone John",
                    "show-birthday John",
                    "show-birthday Anna",
                    "close",
                ]
            )

        self.assertEqual(second_session[0], "Welcome to the assistant bot!")
        self.assertTrue(
            any(
                "Contact name: John, phones: 1234567890; 0987654321, "
                "birthday: 07.11.1990" in line
                for line in second_session
            )
        )
        self.assertTrue(
            any(
                "Contact name: Anna, phones: 5555555555" in line
                for line in second_session
            )
        )
        self.assertIn("1234567890; 0987654321", second_session)
        self.assertIn("07.11.1990", second_session)
        self.assertIn("No birthday saved for Anna.", second_session)
        self.assertEqual(second_session[-1], "Good bye!")

    def test_startup_without_a_storage_file(self):
        with temporary_directory() as directory:
            printed = self._run(["all", "exit"])
            filename = os.path.join(directory, "addressbook.pkl")

            self.assertEqual(
                printed,
                [
                    "Welcome to the assistant bot!",
                    "No contacts found.",
                    "Good bye!",
                ],
            )
            self.assertTrue(os.path.isfile(filename))
            self.assertEqual(len(load_data(filename).data), 0)

    def test_interrupted_session_still_saves_the_book(self):
        with temporary_directory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            with self.assertRaises(KeyboardInterrupt):
                self._run(["add John 1234567890", KeyboardInterrupt()])

            restored = load_data(filename)

        self.assertEqual(restored.find("John").phones[0].value, "1234567890")

    def test_corrupted_storage_is_reported_and_left_unchanged(self):
        with temporary_directory() as directory:
            filename = os.path.join(directory, "addressbook.pkl")

            with open(filename, "wb") as file:
                file.write(b"broken")

            printed = []

            with self.assertRaises(SystemExit) as error:
                self._run(["add John 1234567890", "exit"], printed)

            with open(filename, "rb") as file:
                contents = file.read()

        self.assertEqual(error.exception.code, 1)
        self.assertEqual(contents, b"broken")
        self.assertEqual(len(printed), 1)
        self.assertIn("corrupted or incompatible", printed[0])
        self.assertNotIn("Welcome to the assistant bot!", printed)
        self.assertNotIn("Good bye!", printed)


if __name__ == "__main__":
    unittest.main()
