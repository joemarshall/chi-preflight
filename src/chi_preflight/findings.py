from dataclasses import dataclass
from enum import IntEnum


class Level(IntEnum):
    INFO = 0
    WARNING = 1
    ERROR = 2


@dataclass
class Finding:
    level: Level
    checker: str
    target: str
    message: str
    category: str = "general"

    def __str__(self):
        return f"[{self.level.name}] [{self.category}] {self.checker}: {self.target}: {self.message}"
