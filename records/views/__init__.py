# Import all view functions to maintain compatibility with existing urls.py
from .dashboard_views import dashboard, admin_user_dashboard
from .timeblock_views import add_timeblock, edit_timeblock, delete_timeblock
from .timeentry_views import add_time_entry, edit_time_entry, delete_time_entry
from .report_views import monthly_report, export_monthly_csv
from .signoff_views import (
    signoff_management,
    signoff_month,
    unsignoff_month,
    signoff_report,
    unsignoff_report,
)
from .rota_views import (
    rota_calendar,
    add_staff_to_rota,
    toggle_shift_type,
    clear_day_staff,
    create_rota_entry,
    remove_staff_from_rota,
    rota_statistics,
)