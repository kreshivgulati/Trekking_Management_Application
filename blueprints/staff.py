from flask import Blueprint, render_template
from flask_login import login_required, current_user

from models import Trek, RoleEnum
from decorators import role_required

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@role_required(RoleEnum.STAFF)
def dashboard():
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=current_user.id
    ).all()
    return render_template("staff/dashboard.html", assigned_treks=assigned_treks)