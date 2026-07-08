from datetime import datetime

from database import db
from models.enums import DifficultyEnum, TrekStatusEnum


class Trek(db.Model):
    __tablename__ = "treks"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(150), nullable=False)
    difficulty = db.Column(db.Enum(DifficultyEnum), nullable=False,
                            default=DifficultyEnum.EASY)
    duration_days = db.Column(db.Integer, nullable=False)

    total_slots = db.Column(db.Integer, nullable=False)
    available_slots = db.Column(db.Integer, nullable=False)

    assigned_staff_id = db.Column(db.Integer, db.ForeignKey("users.id"),
                                   nullable=True)

    status = db.Column(db.Enum(TrekStatusEnum), nullable=False,
                        default=TrekStatusEnum.PENDING)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_staff = db.relationship(
        "User", back_populates="assigned_treks",
        foreign_keys=[assigned_staff_id]
    )
    bookings = db.relationship(
        "Booking", back_populates="trek",
        foreign_keys="Booking.trek_id",
        cascade="all, delete-orphan"
    )

    def has_available_slot(self):
        return self.status in (TrekStatusEnum.APPROVED, TrekStatusEnum.OPEN) and self.available_slots > 0

    def update_status(self, new_status):
        from models.enums import TrekStatusEnum, BookingStatusEnum
        self.status = new_status
        if new_status == TrekStatusEnum.COMPLETED:
            for booking in self.bookings:
                if booking.status == BookingStatusEnum.BOOKED:
                    booking.status = BookingStatusEnum.COMPLETED
        elif new_status == TrekStatusEnum.CLOSED:
            for booking in self.bookings:
                if booking.status == BookingStatusEnum.BOOKED:
                    booking.status = BookingStatusEnum.CANCELLED
                    self.available_slots += 1

    def __repr__(self):
        return f"<Trek {self.id} {self.name} status={self.status.value}>"