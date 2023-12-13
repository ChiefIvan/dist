from typing import Final
from dotenv import load_dotenv
from os import getenv
from os.path import join, dirname

dotenv_path = join(dirname(__file__), "../", ".env")
load_dotenv(dotenv_path)

EMAIL: Final[str] = getenv("EMAIL")
PASSWORD: Final[str] = getenv("PASSWORD")
