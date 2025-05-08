import enum


class PositionEnum(enum.Enum):
    DEVELOPER = "разработчик"
    TEAM_LEAD = "тимлид"
    HEAD = "руководитель направления"


__all__ = [
    "PositionEnum",
]
