from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import login_required

from database import db
from models import User, Trek, Booking, RoleEnum, UserStatusEnum
from decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required(RoleEnum.ADMIN)
def dashboard():
    context = {
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role=RoleEnum.TREKKER).count(),
        "total_staff": User.query.filter_by(role=RoleEnum.STAFF).count(),
        "total_bookings": Booking.query.count(),
        "pending_staff": User.query.filter_by(
            role=RoleEnum.STAFF, is_approved=False
        ).all(),
    }
    return render_template("admin/dashboard.html", **context)


@admin_bp.route("/approve-staff/<int:user_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def approve_staff(user_id):
    staff = User.query.get_or_404(user_id)
    if staff.role != RoleEnum.STAFF:
        flash("That user is not a staff account.", "danger")
        return redirect(url_for("admin.dashboard"))

    staff.is_approved = True
    db.session.commit()
    flash(f"{staff.name} has been approved.", "success")
    return redirect(url_for("admin.dashboard"))


@admin_bp.route("/blacklist/<int:user_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == RoleEnum.ADMIN:
        flash("You cannot blacklist an admin account.", "danger")
        return redirect(url_for("admin.dashboard"))

    user.status = UserStatusEnum.BLACKLISTED
    db.session.commit()
    flash(f"{user.name} has been blacklisted.", "warning")
    return redirect(url_for("admin.dashboard"))