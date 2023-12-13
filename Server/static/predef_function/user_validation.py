from re import compile
from bleach.sanitizer import Cleaner


class EntryValidator:
    def __init__(self, entries: dict):
        self.entries = entries

    def validate(self) -> bool | dict:

        length_error: str = "Your Firstname must be greater than 3 Characters"
        error_responses: dict = {
            "userName": "Username Entry is Empty!",
            "email": "Email Entry is Empty!",
            "password": "Password Entry is Empty!",
        }

        for key, value in self.entries.items():
            if value is not None:
                if len(value) == 0:

                    return {
                        "error": error_responses.get
                        (key, "Password Confirmation is Empty!")
                    }

        if self.entries["userName"] is not None:
            if len(self.entries["userName"]) < 4:
                return {"error": length_error}

        return True


class RegisterEntryValidator:
    def __init__(self, *args):
        self.args = args

    def validate(self):
        length_error: str = "Please fill all Entries"

        for data in self.args:
            if data is not None and len(data) == 0:
                return {"error": length_error}


class Sanitizer:
    def __init__(self, entries: dict):

        self.entries = entries
        self.cleaner = Cleaner(tags=[])

    def validate(self) -> bool | dict:
        invalid_characters: str = "Invalid Characters found:"

        for key, value in self.entries.items():
            if value is not None:
                if self.cleaner.clean(value) != value:
                    return {"error": f"{invalid_characters} {value}"}

        return True


class EmailValidator:
    def __init__(self, entries: dict):
        self.entries = entries

    def validate(self) -> bool | dict:

        email_format_error: str = "Your Email Format is Invalid."
        pattern = compile(
            r'^[a-zA-Z0-9._%+-]{5,}@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

        if not pattern.match(self.entries["email"]):
            return {"error": email_format_error}

        return True


class PasswordValidator:
    def __init__(self, entries: dict):
        self.entries = entries

    def validate(self) -> bool | dict:

        length_error: str = "Your Password must be greater than 7 Characters!"
        combination_error: str = "Your Password have atleast 1 Uppercase, 1 Lowercase and a Number"
        password_error: str = "Your Password and Confirmation Password must be the same!"
        pattern = compile(r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9]).*$")

        for key, value in self.entries.items():
            if value is not None:
                if key == "password":
                    if len(value) < 8:
                        return {"error": length_error}

                    if not pattern.match(value):
                        return {"error": combination_error}

        if self.entries["cnfrmPassword"] is not None \
                and self.entries["password"] is not None:

            if self.entries["password"] != self.entries["cnfrmPassword"]:
                return {"error": password_error}

        return True


class UserValidation:
    def __init__(self, entries: dict):

        self.validators = [
            EntryValidator(entries),
            Sanitizer(entries),
            EmailValidator(entries),
            PasswordValidator(entries)
        ]

    def validate_user(self) -> bool | dict:

        for validator in self.validators:
            response: dict | bool = validator.validate()

            if isinstance(response, dict):
                return response

        return True
