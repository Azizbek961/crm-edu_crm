from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('admin/payments/', views.admin_payments_dashboard, name='admin_payments_dashboard'),
    path('', views.payments_dashboard, name='payments_dashboard'),
    path('student/', views.student_payments, name='student_payments'),
    path('add/', views.add_payment, name='add_payment'),
    path('update/<int:payment_id>/', views.update_payment_status, name='update_payment_status'),
]