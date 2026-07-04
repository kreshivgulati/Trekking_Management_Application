from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required, current_user

from database import db
from models import Trek, Booking, RoleEnum, TrekStatusEnum, BookingStatusEnum
from decorators import role_required

trekker_bp = Blueprint("trekker", __name__, url_prefix="/trekker")


@trekker_bp.route("/dashboard")
@login_required
@role_required(RoleEnum.TREKKER)
def dashboard():
    open_treks = Trek.query.filter_by(status=TrekStatusEnum.OPEN).all()
    my_bookings = Booking.query.filter_by(user_id=current_user.id).all()
    return render_template(
        "trekker/dashboard.html",
        open_treks=open_treks,
        my_bookings=my_bookings,
    )


@trekker_bp.route("/book/<int:trek_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.TREKKER)
def book_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)

    # Re-query slot state right before committing to guard against the
    # overbooking race the assignment spec explicitly calls out — two
    # trekkers booking the last slot at nearly the same time.
    if not trek.has_available_slot():
        flash("Sorry, this trek is no longer open or has no slots left.", "danger")
        return redirect(url_for("trekker.dashboard"))

    existing = Booking.query.filter_by(
        user_id=current_user.id, trek_id=trek.id, status=BookingStatusEnum.BOOKED
    ).first()
    if existing:
        flash("You already have an active booking for this trek.", "warning")
        return redirect(url_for("trekker.dashboard"))

    trek.available_slots -= 1
    booking = Booking(user_id=current_user.id, trek_id=trek.id,
                       status=BookingStatusEnum.BOOKED)
    db.session.add(booking)
    db.session.commit()

    flash(f"Booked {trek.name}!", "success")
    return redirect(url_for("trekker.dashboard"))


@trekker_bp.route("/cancel/<int:booking_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.TREKKER)
def cancel_booking(booking_id):
    booking = Booking.query.get_or_404(booking_id)

    if booking.user_id != current_user.id:
        flash("You can only cancel your own bookings.", "danger")
        return redirect(url_for("trekker.dashboard"))

    if booking.status != BookingStatusEnum.BOOKED:
        flash("This booking can't be cancelled.", "warning")
        return redirect(url_for("trekker.dashboard"))

    booking.status = BookingStatusEnum.CANCELLED
    booking.trek.available_slots += 1
    db.session.commit()

    flash("Booking cancelled.", "info")
    return redirect(url_for("trekker.dashboard"))