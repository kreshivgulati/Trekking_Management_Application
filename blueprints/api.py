from flask import Blueprint, jsonify, abort
from flask_login import login_required, current_user

from models import Trek, Booking, User, RoleEnum, TrekStatusEnum, BookingStatusEnum

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/treks", methods=["GET"])
@login_required
def get_treks():
    """
    Returns lists of treks.
    Admin gets all treks.
    Staff and Trekker get only APPROVED/OPEN/CLOSED/COMPLETED treks.
    """
    if current_user.role == RoleEnum.ADMIN:
        treks = Trek.query.all()
    else:
        treks = Trek.query.filter(Trek.status != TrekStatusEnum.PENDING).all()
        
    return jsonify({
        "status": "success",
        "data": [{
            "id": t.id,
            "name": t.name,
            "location": t.location,
            "difficulty": t.difficulty.value,
            "duration_days": t.duration_days,
            "total_slots": t.total_slots,
            "available_slots": t.available_slots,
            "status": t.status.value,
            "start_date": t.start_date.isoformat(),
            "end_date": t.end_date.isoformat(),
            "assigned_staff_id": t.assigned_staff_id,
            "assigned_staff_name": t.assigned_staff.name if t.assigned_staff else None
        } for t in treks]
    })


@api_bp.route("/treks/<int:trek_id>", methods=["GET"])
@login_required
def get_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    
    # Trekkers / Staff can't view pending treks
    if current_user.role != RoleEnum.ADMIN and trek.status == TrekStatusEnum.PENDING:
        abort(403)
        
    return jsonify({
        "status": "success",
        "data": {
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty.value,
            "duration_days": trek.duration_days,
            "total_slots": trek.total_slots,
            "available_slots": trek.available_slots,
            "status": trek.status.value,
            "start_date": trek.start_date.isoformat(),
            "end_date": trek.end_date.isoformat(),
            "assigned_staff_id": trek.assigned_staff_id,
            "assigned_staff_name": trek.assigned_staff.name if trek.assigned_staff else None
        }
    })


@api_bp.route("/bookings", methods=["GET"])
@login_required
def get_bookings():
    """
    Returns list of bookings based on roles:
    Admin: all bookings.
    Staff: bookings for treks they are assigned to.
    Trekker: their own bookings.
    """
    if current_user.role == RoleEnum.ADMIN:
        bookings = Booking.query.all()
    elif current_user.role == RoleEnum.STAFF:
        bookings = Booking.query.join(Trek).filter(Trek.assigned_staff_id == current_user.id).all()
    else:
        bookings = Booking.query.filter_by(user_id=current_user.id).all()
        
    return jsonify({
        "status": "success",
        "data": [{
            "id": b.id,
            "user_id": b.user_id,
            "user_name": b.user.name,
            "trek_id": b.trek_id,
            "trek_name": b.trek.name,
            "booking_date": b.booking_date.isoformat(),
            "status": b.status.value
        } for b in bookings]
    })


@api_bp.route("/users", methods=["GET"])
@login_required
def get_users():
    """
    Returns list of users. Admin only.
    """
    if current_user.role != RoleEnum.ADMIN:
        abort(403)
        
    users = User.query.filter(User.role != RoleEnum.ADMIN).all()
    return jsonify({
        "status": "success",
        "data": [{
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role.value,
            "status": u.status.value,
            "is_approved": u.is_approved
        } for u in users]
    })
