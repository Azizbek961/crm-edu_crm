from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime
from .models import Fee
from users.models import Student
from django.contrib.auth import get_user_model

User = get_user_model()


@login_required
def admin_payments_dashboard(request):
    # Umumiy statistik ma'lumotlar
    total_revenue = Fee.objects.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    pending_payments = Fee.objects.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0

    # Oylik to'lovlar (joriy oy)
    current_month = timezone.now().month
    current_year = timezone.now().year
    paid_this_month = Fee.objects.filter(
        status='paid',
        paid_date__month=current_month,
        paid_date__year=current_year
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    overdue_payments = Fee.objects.filter(
        status='overdue'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Filtrlash va qidirish
    status_filter = request.GET.get('status', 'all')
    student_filter = request.GET.get('student', 'all')
    search_query = request.GET.get('search', '')

    # Barcha to'lovlarni olish
    payments = Fee.objects.all().order_by('-due_date')

    # Status bo'yicha filtrlash
    if status_filter != 'all':
        payments = payments.filter(status=status_filter)

    # Talaba bo'yicha filtrlash
    if student_filter != 'all':
        payments = payments.filter(student_id=student_filter)

    # Qidirish
    if search_query:
        payments = payments.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query)
        )

    # Barcha talabalarni olish (filter uchun)
    students = Student.objects.all()

    context = {
        'payments': payments,
        'students': students,
        'total_revenue': total_revenue,
        'pending_payments': pending_payments,
        'paid_this_month': paid_this_month,
        'overdue_payments': overdue_payments,
        'selected_status': status_filter,
        'selected_student': student_filter,
        'search_query': search_query,
    }

    return render(request, 'admin/admin_payments.html', context)


@login_required
def add_payment(request):
    if request.method == 'POST':
        student_id = request.POST.get('student')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        paid_date = request.POST.get('paid_date') or None
        description = request.POST.get('description')
        status = request.POST.get('status')

        # Statusni avtomatik aniqlash
        if status == 'paid' and not paid_date:
            paid_date = timezone.now().date()

        # To'lovni yaratish
        Fee.objects.create(
            student_id=student_id,
            amount=amount,
            due_date=due_date,
            paid_date=paid_date,
            status=status
        )

        # TO'G'RILANGAN QISMI: payments:payments_dashboard deb to'g'ri yozildi
        return redirect('payments:payments_dashboard')

    return redirect('payments:payments_dashboard')


@login_required
def update_payment_status(request, payment_id):
    payment = get_object_or_404(Fee, id=payment_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        payment.status = new_status

        # Agar to'lov 'paid' holatiga o'zgarsa, paid_date ni yangilash
        if new_status == 'paid' and not payment.paid_date:
            payment.paid_date = timezone.now().date()

        payment.save()

    return redirect('payments:payments_dashboard')


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime
from .models import Fee
from users.models import Student
from django.contrib.auth import get_user_model
from .forms import FeePaymentForm
from django.contrib import messages

User = get_user_model()


@login_required
def payments_dashboard(request):
    # Check if user is a student
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Access denied. Students only.")
        return redirect('admin_dashboard')

    student = request.user.student_profile

    # Get student's payment statistics
    student_fees = Fee.objects.filter(student=student)

    total_paid = student_fees.filter(status='paid').aggregate(Sum('amount'))['amount__sum'] or 0
    completed_payments = student_fees.filter(status='paid').count()
    pending_payments = student_fees.filter(status='pending').count()
    overdue_payments = student_fees.filter(status='overdue').count()

    # Get pending fees (not paid)
    pending_fees = student_fees.filter(status__in=['pending', 'overdue']).order_by('due_date')

    # Get payment history (paid fees)
    payment_history = student_fees.filter(status='paid').order_by('-paid_date')

    context = {
        'student': student,
        'total_paid': total_paid,
        'completed_payments': completed_payments,
        'pending_payments': pending_payments,
        'overdue_payments': overdue_payments,
        'pending_fees': pending_fees,
        'payment_history': payment_history,
    }

    return render(request, 'student/student_payment.html', context)


@login_required
def add_payment(request):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Access denied. Students only.")
        return redirect('users:dashboard')

    if request.method == 'POST':
        student = request.user.student_profile
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        paid_date = request.POST.get('paid_date') or None
        description = request.POST.get('description')
        status = request.POST.get('status')

        if status == 'paid' and not paid_date:
            paid_date = timezone.now().date()

        Fee.objects.create(
            student=student,
            amount=amount,
            due_date=due_date,
            paid_date=paid_date,
            status=status
        )

        messages.success(request, "Payment added successfully!")
        return redirect('payments:student_payments')

    return redirect('payments:student_payments')

# Add this new view for student payments
@login_required
def student_payments(request):
    if not hasattr(request.user, 'student_profile'):
        messages.error(request, "Access denied. Students only.")
        return redirect('users:dashboard')

    return payments_dashboard(request)