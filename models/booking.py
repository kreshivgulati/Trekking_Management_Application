from datetime import datetime

from database import db
from models.enums import BookingStatusEnum


class Booking(db.Model):
    __tablename__ = "bookings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    trek_id = db.Column(db.Integer, db.ForeignKey("treks.id"), nullable=False)

    booking_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.Enum(BookingStatusEnum), nullable=False,
                        default=BookingStatusEnum.BOOKED)

    user = db.relationship("User", back_populates="bookings",
                            foreign_keys=[user_id])
    trek = db.relationship("Trek", back_populates="bookings",
                            foreign_keys=[trek_id])

    def __repr__(self):
        return f"<Booking {self.id} user={self.user_id} trek={self.trek_id} status={self.status.value}>"