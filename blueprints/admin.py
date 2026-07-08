from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required

from database import db
from models import (
    User, Trek, Booking, RoleEnum, UserStatusEnum,
    DifficultyEnum, TrekStatusEnum, BookingStatusEnum
)
from decorators import role_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required(RoleEnum.ADMIN)
def dashboard():
    # Gather statistics for display
    easy_count = Trek.query.filter_by(difficulty=DifficultyEnum.EASY).count()
    moderate_count = Trek.query.filter_by(difficulty=DifficultyEnum.MODERATE).count()
    hard_count = Trek.query.filter_by(difficulty=DifficultyEnum.HARD).count()

    booked_count = Booking.query.filter_by(status=BookingStatusEnum.BOOKED).count()
    cancelled_count = Booking.query.filter_by(status=BookingStatusEnum.CANCELLED).count()
    completed_count = Booking.query.filter_by(status=BookingStatusEnum.COMPLETED).count()

    context = {
        "total_treks": Trek.query.count(),
        "total_users": User.query.filter_by(role=RoleEnum.TREKKER).count(),
        "total_staff": User.query.filter_by(role=RoleEnum.STAFF).count(),
        "total_bookings": Booking.query.count(),
        "pending_staff": User.query.filter_by(
            role=RoleEnum.STAFF, is_approved=False
        ).all(),
        # Stats for charts
        "easy_count": easy_count,
        "moderate_count": moderate_count,
        "hard_count": hard_count,
        "booked_count": booked_count,
        "cancelled_count": cancelled_count,
        "completed_count": completed_count,
    }
    return render_template("admin/dashboard.html", **context)


@admin_bp.route("/approve-staff/<int:user_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def approve_staff(user_id):
    staff = User.query.get_or_404(user_id)
    if staff.role != RoleEnum.STAFF:
        flash("That user is not a staff account.", "danger")
        return redirect(request.referrer or url_for("admin.dashboard"))

    staff.is_approved = True
    db.session.commit()
    flash(f"{staff.name} has been approved.", "success")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/blacklist/<int:user_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def blacklist_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == RoleEnum.ADMIN:
        flash("You cannot blacklist an admin account.", "danger")
        return redirect(request.referrer or url_for("admin.dashboard"))

    user.status = UserStatusEnum.BLACKLISTED
    db.session.commit()
    flash(f"{user.name} has been blacklisted.", "warning")
    return redirect(request.referrer or url_for("admin.dashboard"))


@admin_bp.route("/treks", methods=["GET"])
@login_required
@role_required(RoleEnum.ADMIN)
def manage_treks():
    search_query = request.args.get("q", "").strip()
    
    query = Trek.query
    if search_query:
        if search_query.isdigit():
            query = query.filter(
                (Trek.id == int(search_query)) |
                (Trek.name.like(f"%{search_query}%")) |
                (Trek.location.like(f"%{search_query}%"))
            )
        else:
            query = query.filter(
                (Trek.name.like(f"%{search_query}%")) |
                (Trek.location.like(f"%{search_query}%"))
            )
            
    treks = query.order_by(Trek.id.asc()).all()
    
    # Need approved and active staff list to assign in forms
    active_staff = User.query.filter_by(
        role=RoleEnum.STAFF, is_approved=True, status=UserStatusEnum.ACTIVE
    ).all()
    
    return render_template(
        "admin/treks.html",
        treks=treks,
        active_staff=active_staff,
        difficulties=DifficultyEnum,
        statuses=TrekStatusEnum,
        search_query=search_query
    )


@admin_bp.route("/treks/create", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def create_trek():
    from datetime import datetime
    
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    difficulty_val = request.form.get("difficulty", "")
    duration_days_val = request.form.get("duration_days", "")
    total_slots_val = request.form.get("total_slots", "")
    start_date_val = request.form.get("start_date", "")
    end_date_val = request.form.get("end_date", "")
    assigned_staff_id_val = request.form.get("assigned_staff_id", "")
    status_val = request.form.get("status", "")
    
    if not name or not location or not difficulty_val or not duration_days_val or not total_slots_val or not start_date_val or not end_date_val or not status_val:
        flash("All fields except staff are required.", "danger")
        return redirect(url_for("admin.manage_treks"))
        
    try:
        difficulty = DifficultyEnum(difficulty_val)
        duration_days = int(duration_days_val)
        total_slots = int(total_slots_val)
        start_date = datetime.strptime(start_date_val, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_val, "%Y-%m-%d").date()
        status = TrekStatusEnum(status_val)
        
        assigned_staff_id = None
        if assigned_staff_id_val:
            assigned_staff_id = int(assigned_staff_id_val)
            
        if duration_days <= 0 or total_slots <= 0:
            flash("Duration and slots must be positive numbers.", "danger")
            return redirect(url_for("admin.manage_treks"))
            
        if end_date < start_date:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("admin.manage_treks"))
            
        trek = Trek(
            name=name,
            location=location,
            difficulty=difficulty,
            duration_days=duration_days,
            total_slots=total_slots,
            available_slots=total_slots,
            assigned_staff_id=assigned_staff_id,
            status=status,
            start_date=start_date,
            end_date=end_date
        )
        
        db.session.add(trek)
        db.session.commit()
        
        if trek.status == TrekStatusEnum.COMPLETED:
            trek.update_status(TrekStatusEnum.COMPLETED)
            db.session.commit()
            
        flash(f"Trek '{name}' created successfully.", "success")
    except ValueError as e:
        flash(f"Invalid input data: {str(e)}", "danger")
        
    return redirect(url_for("admin.manage_treks"))


@admin_bp.route("/treks/edit/<int:trek_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def edit_trek(trek_id):
    from datetime import datetime
    
    trek = Trek.query.get_or_404(trek_id)
    
    name = request.form.get("name", "").strip()
    location = request.form.get("location", "").strip()
    difficulty_val = request.form.get("difficulty", "")
    duration_days_val = request.form.get("duration_days", "")
    total_slots_val = request.form.get("total_slots", "")
    start_date_val = request.form.get("start_date", "")
    end_date_val = request.form.get("end_date", "")
    assigned_staff_id_val = request.form.get("assigned_staff_id", "")
    status_val = request.form.get("status", "")
    
    if not name or not location or not difficulty_val or not duration_days_val or not total_slots_val or not start_date_val or not end_date_val or not status_val:
        flash("All fields except staff are required.", "danger")
        return redirect(url_for("admin.manage_treks"))
        
    try:
        difficulty = DifficultyEnum(difficulty_val)
        duration_days = int(duration_days_val)
        total_slots = int(total_slots_val)
        start_date = datetime.strptime(start_date_val, "%Y-%m-%d").date()
        end_date = datetime.strptime(end_date_val, "%Y-%m-%d").date()
        status = TrekStatusEnum(status_val)
        
        assigned_staff_id = None
        if assigned_staff_id_val:
            assigned_staff_id = int(assigned_staff_id_val)
            
        if duration_days <= 0 or total_slots <= 0:
            flash("Duration and slots must be positive numbers.", "danger")
            return redirect(url_for("admin.manage_treks"))
            
        if end_date < start_date:
            flash("End date cannot be before start date.", "danger")
            return redirect(url_for("admin.manage_treks"))
            
        active_bookings_count = Booking.query.filter_by(
            trek_id=trek.id, status=BookingStatusEnum.BOOKED
        ).count()
        
        if total_slots < active_bookings_count:
            flash(f"Cannot reduce total slots to {total_slots} because there are already {active_bookings_count} active bookings.", "danger")
            return redirect(url_for("admin.manage_treks"))
            
        trek.name = name
        trek.location = location
        trek.difficulty = difficulty
        trek.duration_days = duration_days
        trek.total_slots = total_slots
        trek.available_slots = total_slots - active_bookings_count
        trek.assigned_staff_id = assigned_staff_id
        trek.start_date = start_date
        trek.end_date = end_date
        
        trek.update_status(status)
        
        db.session.commit()
        flash(f"Trek '{name}' updated successfully.", "success")
    except ValueError as e:
        flash(f"Invalid input data: {str(e)}", "danger")
        
    return redirect(url_for("admin.manage_treks"))


@admin_bp.route("/treks/delete/<int:trek_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def delete_trek(trek_id):
    trek = Trek.query.get_or_404(trek_id)
    name = trek.name
    db.session.delete(trek)
    db.session.commit()
    flash(f"Trek '{name}' has been deleted.", "success")
    return redirect(url_for("admin.manage_treks"))


@admin_bp.route("/users", methods=["GET"])
@login_required
@role_required(RoleEnum.ADMIN)
def manage_users():
    search_query = request.args.get("q", "").strip()
    role_filter = request.args.get("role", "")
    
    query = User.query.filter(User.role != RoleEnum.ADMIN)
    
    if role_filter:
        try:
            query = query.filter_by(role=RoleEnum(role_filter))
        except ValueError:
            pass
            
    if search_query:
        if search_query.isdigit():
            query = query.filter(
                (User.id == int(search_query)) |
                (User.name.like(f"%{search_query}%")) |
                (User.email.like(f"%{search_query}%")) |
                (User.phone.like(f"%{search_query}%"))
            )
        else:
            query = query.filter(
                (User.name.like(f"%{search_query}%")) |
                (User.email.like(f"%{search_query}%")) |
                (User.phone.like(f"%{search_query}%"))
            )
            
    users = query.order_by(User.id.asc()).all()
    
    return render_template(
        "admin/users.html",
        users=users,
        search_query=search_query,
        role_filter=role_filter,
        roles=RoleEnum
    )


@admin_bp.route("/users/toggle-status/<int:user_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def toggle_user_status(user_id):
    user = User.query.get_or_404(user_id)
    if user.role == RoleEnum.ADMIN:
        flash("Cannot modify admin status.", "danger")
        return redirect(url_for("admin.manage_users"))
        
    if user.status == UserStatusEnum.ACTIVE:
        user.status = UserStatusEnum.BLACKLISTED
        flash(f"{user.name} has been blacklisted.", "warning")
    else:
        user.status = UserStatusEnum.ACTIVE
        flash(f"{user.name} is now active.", "success")
        
    db.session.commit()
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/users/toggle-approval/<int:user_id>", methods=["POST"])
@login_required
@role_required(RoleEnum.ADMIN)
def toggle_staff_approval(user_id):
    user = User.query.get_or_404(user_id)
    if user.role != RoleEnum.STAFF:
        flash("User is not a staff member.", "danger")
        return redirect(url_for("admin.manage_users"))
        
    user.is_approved = not user.is_approved
    db.session.commit()
    status_str = "approved" if user.is_approved else "unapproved"
    flash(f"Staff member {user.name} status set to {status_str}.", "success")
    return redirect(url_for("admin.manage_users"))


@admin_bp.route("/bookings", methods=["GET"])
@login_required
@role_required(RoleEnum.ADMIN)
def view_bookings():
    search_query = request.args.get("q", "").strip()
    status_filter = request.args.get("status", "")
    
    query = Booking.query
    
    if status_filter:
        try:
            query = query.filter_by(status=BookingStatusEnum(status_filter))
        except ValueError:
            pass
            
    if search_query:
        query = query.join(User).join(Trek)
        if search_query.isdigit():
            query = query.filter(
                (Booking.id == int(search_query)) |
                (User.name.like(f"%{search_query}%")) |
                (Trek.name.like(f"%{search_query}%"))
            )
        else:
            query = query.filter(
                (User.name.like(f"%{search_query}%")) |
                (Trek.name.like(f"%{search_query}%"))
            )
            
    bookings = query.order_by(Booking.id.asc()).all()
    
    return render_template(
        "admin/bookings.html",
        bookings=bookings,
        search_query=search_query,
        status_filter=status_filter,
        statuses=BookingStatusEnum
    )