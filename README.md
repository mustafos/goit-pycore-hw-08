# Тема 12. Домашня робота. Серіалізація та копіювання об'єктів у Python

## Завдання

Консольний бот уже веде адресну книгу в пам'яті. Ця робота додає збереження книги на диск і відновлення з диска.

Протокол серіалізації — `pickle`. У файл записується весь об'єкт `AddressBook`, з яким працювала програма. Після виходу контакти не зникають. Наступний запуск відкриває ту саму книгу.

## Критерії оцінювання

| Критерій | Де виконано |
| --- | --- |
| Серіалізація та десеріалізація через `pickle` | `save_data` викликає `pickle.dump`, `load_data` викликає `pickle.load` |
| Усі дані зберігаються під час виходу | `main` викликає `save_data(book)` перед завершенням |
| Новий сеанс відкриває книгу з попереднього запуску | `main` на старті викликає `book = load_data()` |

## Як працює збереження

`pickle` перетворює об'єкт Python на байти і може зібрати цей об'єкт знову.

Серіалізація — це запис. `save_data` відкриває `addressbook.pkl` у бінарному режимі `"wb"` і передає в `pickle.dump` сам об'єкт `AddressBook`. У файлі опиняються контакти, телефони й дні народження.

Десеріалізація — це читання. `load_data` відкриває файл у режимі `"rb"` і викликає `pickle.load`. Повертається екземпляр `AddressBook`.

```python
def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(book, file)

def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as file:
            return pickle.load(file)
    except FileNotFoundError:
        return AddressBook()
```

Якщо файлу ще немає, `load_data` перехоплює `FileNotFoundError` і повертає нову порожню `AddressBook`. Так програма поводиться під час першого запуску. Якщо файл пошкоджений, програма повідомляє про це і не замінює його порожньою книгою.

`main` спочатку завантажує книгу і працює з цим самим об'єктом. Перед завершенням книга записується один раз:

```python
def main():
    book = load_data()

    try:
        while True:
            # add, change, phone, all, add-birthday, ...
            if command in ("close", "exit"):
                break
    finally:
        save_data(book)
```

`close` і `exit` виходять із циклу, після чого `finally` викликає `save_data`. Файл з'являється в поточній теці.

Файл `addressbook.pkl` створюється під час роботи програми і містить особисті контакти, тому `.gitignore` не додає його в Git.

## Структура

```text
goit-pycore-hw-08/
├── address_book.py    # AddressBook, Record, Field, Name, Phone, Birthday
├── bot.py             # Команди бота
├── storage.py         # save_data і load_data
├── main.py            # Завантаження на старті і запис перед виходом
├── test_storage.py    # Перевірка збереження і відновлення
└── README.md
```

## Запуск

Потрібен Python 3.9 або новіший. Сторонні пакети не потрібні: `pickle` входить до стандартної бібліотеки.

```bash
git clone git@github.com:mustafos/goit-pycore-hw-08.git
cd goit-pycore-hw-08
python3 main.py
```

## Приклад

Перший запуск додає контакти. Команда `exit` зберігає книгу:

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

Другий запуск у тій самій теці показує книгу з попереднього сеансу:

```text
Welcome to the assistant bot!
Enter a command: all
Contact name: John, phones: 1234567890; 0987654321, birthday: 07.11.1990
Contact name: Anna, phones: 5555555555
Enter a command: show-birthday John
07.11.1990
Enter a command: close
Good bye!
```

## Команди бота

| Команда | Приклад | Дія |
| --- | --- | --- |
| `add` | `add John 1234567890` | Додає контакт або ще один телефон |
| `change` | `change John 1234567890 0987654321` | Замінює телефон |
| `phone` | `phone John` | Показує телефони контакту |
| `all` | `all` | Показує всю книгу |
| `add-birthday` | `add-birthday John 07.11.1990` | Зберігає день народження |
| `show-birthday` | `show-birthday John` | Показує день народження |
| `birthdays` | `birthdays` | Показує привітання на 7 днів |
| `close`, `exit` | `exit` | Зберігає книгу і завершує програму |

## Тести

```bash
python3 -m unittest discover -v
```

Тести перевіряють запис книги, читання з файлу, кілька контактів, телефони, дні народження, відсутній файл і повторний запуск програми. Вони працюють у тимчасових теках і не змінюють `addressbook.pkl` у теці проєкту.
