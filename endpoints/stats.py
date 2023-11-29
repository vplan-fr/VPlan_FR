
from flask import Blueprint
from flask_login import login_required

from utils import send_success, is_admin
from datascience.user_creation import get_monthly_signups, get_settings_usage

stats = Blueprint('stats', __name__)


@stats.route('/monthly_signups')
@login_required
@is_admin
def signups():
    return send_success(get_monthly_signups())

# next up:
# - get_users_by_time
# - get_school_counts
# - get base requests per day
# - Belas matplotlib stats
# - stats per time of day


@stats.route('/settings_usage')
@login_required
@is_admin
def settings_usage():
    return send_success(get_settings_usage())
