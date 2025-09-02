from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('shift/add/', views.add_shift, name='add_shift'),
    path('shift/<int:shift_id>/edit/', views.edit_shift, name='edit_shift'),
    path('shift/<int:shift_id>/delete/', views.delete_shift, name='delete_shift'),
    path('shift/<int:shift_id>/add-entry/', views.add_time_entry, name='add_time_entry'),
    path('entry/<int:entry_id>/edit/', views.edit_time_entry, name='edit_time_entry'),
    path('entry/<int:entry_id>/delete/', views.delete_time_entry, name='delete_time_entry'),
    path('report/', views.monthly_report, name='monthly_report'),
    path('report/export/', views.export_monthly_csv, name='export_monthly_csv'),
    path('staff/user/<int:user_id>/', views.admin_user_dashboard, name='admin_user_dashboard'),
]