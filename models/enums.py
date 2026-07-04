from enum import Enum as PyEnum


class RoleEnum(PyEnum):
    ADMIN = "admin"
    STAFF = "staff"
    TREKKER = "trekker"


class UserStatusEnum(PyEnum):
    ACTIVE = "active"
    BLACKLISTED = "blacklisted"


class DifficultyEnum(PyEnum):
    EASY = "Easy"
    MODERATE = "Moderate"
    HARD = "Hard"


class TrekStatusEnum(PyEnum):
    PENDING = "Pending"
    APPROVED = "Approved"
    OPEN = "Open"
    CLOSED = "Closed"
    COMPLETED = "Completed"


class BookingStatusEnum(PyEnum):
    BOOKED = "Booked"
    CANCELLED = "Cancelled"
    COMPLETED = "Completed"