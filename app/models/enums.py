from enum import Enum

from sqlalchemy import Enum as SAEnum


def enum_values(enum_cls: type[Enum]) -> list[str]:
    return [member.value for member in enum_cls]


def sql_enum(enum_cls: type[Enum], name: str) -> SAEnum:
    return SAEnum(
        enum_cls,
        name=name,
        values_callable=enum_values,
        native_enum=True,
        validate_strings=True,
    )


class UserRole(str, Enum):
    ADMIN = "admin"
    BARBER = "barber"
    USER = "user"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
