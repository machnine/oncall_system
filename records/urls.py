from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('block/add/', views.add_timeblock, name='add_timeblock'),
    path('block/<int:block_id>/edit/', views.edit_timeblock, name='edit_timeblock'),
    path('block/<int:block_id>/delete/', views.delete_timeblock, name='delete_timeblock'),
    path('block/<int:block_id>/add-entry/', views.add_time_entry, name='add_time_entry'),
    path('entry/<int:entry_id>/edit/', views.edit_time_entry, name='edit_time_entry'),
    path('entry/<int:entry_id>/delete/', views.delete_time_entry, name='delete_time_entry'),
    path('report/', views.monthly_report, name='monthly_report'),
    path('report/export/', views.export_monthly_csv, name='export_monthly_csv'),
    path('staff/user/<int:user_id>/', views.admin_user_dashboard, name='admin_user_dashboard'),
    path('signoff/', views.signoff_management, name='signoff_management'),
    path('signoff/<int:staff_id>/<int:year>/<int:month>/', views.signoff_month, name='signoff_month'),
    path('unsignoff/<int:signoff_id>/', views.unsignoff_month, name='unsignoff_month'),
    path('report/signoff/<int:year>/<int:month>/', views.signoff_report, name='signoff_report'),
    path('report/unsignoff/<int:year>/<int:month>/', views.unsignoff_report, name='unsignoff_report'),
    path('rota/', views.rota_calendar, name='rota_calendar'),
    path('rota/add-staff/', views.add_staff_to_rota, name='add_staff_to_rota'),
    path('rota/toggle-shift-type/', views.toggle_shift_type, name='toggle_shift_type'),
    path('rota/clear-day/', views.clear_day_staff, name='clear_day_staff'),
]