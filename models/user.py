from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from database import db
from models.enums import RoleEnum, UserStatusEnum


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    role = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.TREKKER)
    phone = db.Column(db.String(20), nullable=True)

    status = db.Column(db.Enum(UserStatusEnum), nullable=False,
                        default=UserStatusEnum.ACTIVE)
    is_approved = db.Column(db.Boolean, nullable=False, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    assigned_treks = db.relationship(
        "Trek", back_populates="assigned_staff",
        foreign_keys="Trek.assigned_staff_id"
    )
    bookings = db.relationship(
        "Booking", back_populates="user",
        foreign_keys="Booking.user_id"
    )

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_admin(self):
        return self.role == RoleEnum.ADMIN

    @property
    def is_staff(self):
        return self.role == RoleEnum.STAFF

    @property
    def is_trekker(self):
        return self.role == RoleEnum.TREKKER

    @property
    def is_blacklisted(self):
        return self.status == UserStatusEnum.BLACKLISTED

    def can_login(self):
        if self.is_blacklisted:
            return False
        if self.is_staff and not self.is_approved:
            return False
        return True

    def __repr__(self):
        return f"<User {self.id} {self.email} role={self.role.value}>"