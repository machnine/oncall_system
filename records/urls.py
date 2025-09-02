from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('block/add/', views.add_block, name='add_block'),
    path('block/<int:block_id>/edit/', views.edit_block, name='edit_block'),
    path('block/<int:block_id>/delete/', views.delete_block, name='delete_block'),
    path('block/<int:block_id>/add-entry/', views.add_time_entry, name='add_time_entry'),
    path('entry/<int:entry_id>/edit/', views.edit_time_entry, name='edit_time_entry'),
    path('entry/<int:entry_id>/delete/', views.delete_time_entry, name='delete_time_entry'),
    path('report/', views.monthly_report, name='monthly_report'),
    path('report/export/', views.export_monthly_csv, name='export_monthly_csv'),
    path('staff/user/<int:user_id>/', views.admin_user_dashboard, name='admin_user_dashboard'),
]