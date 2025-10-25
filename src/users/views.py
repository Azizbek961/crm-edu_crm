from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView
from django.db.models import Count, Sum, Avg, Q
from education.models import Subject, Homework
from groups.models import Group, Attendance
from exams.models import Exam, Result
from payments.models import Fee
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.utils import timezone
from datetime import timedelta
from .models import Student, User
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from education.models import Subject
import json

from .models import Teacher, User

class CustomLoginView(LoginView):
    template_name = 'login.html'

    def form_valid(self, form):
        # Authenticate user
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(self.request, user)

            # Redirect based on user role
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'teacher':
                return redirect('teacher_dashboard')
            elif user.role == 'student':
                return redirect('student_dashboard')
            elif user.role == 'parent':
                return redirect('parent_dashboard')

        return super().form_invalid(form)

#Dashboar qismi

@login_required
def admin_dashboard(request):
    # Get statistics
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_subjects = Subject.objects.count()

    # Calculate monthly revenue (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    monthly_revenue = Fee.objects.filter(
        paid_date__gte=thirty_days_ago,
        status='paid'
    ).aggregate(Sum('amount'))['amount__sum'] or 0

    # Get recent homework assignments
    recent_homework = Homework.objects.select_related(
        'subject', 'assigned_by', 'assigned_to'
    ).order_by('-created_at')[:5]

    # Get upcoming exams
    upcoming_exams = Exam.objects.select_related(
        'subject', 'group'
    ).filter(date__gte=timezone.now()).order_by('date')[:5]

    # Get today's attendance
    today = timezone.now().date()
    todays_attendance = Attendance.objects.select_related(
        'student', 'group', 'recorded_by'
    ).filter(date=today).order_by('group__name')[:10]

    # Get pending payments
    pending_payments = Fee.objects.select_related('student').filter(
        status='pending'
    ).order_by('due_date')[:10]

    # Performance data for chart (real data from exam results)
    subjects = Subject.objects.all()[:5]
    performance_data = {
        'labels': [subject.name for subject in subjects],
        'data': []
    }

    for subject in subjects:
        avg_score = Result.objects.filter(
            exam__subject=subject
        ).aggregate(Avg('score'))['score__avg'] or 0
        performance_data['data'].append(round(avg_score, 1))

    # Attendance data for chart (real data from attendance records)
    months = []
    attendance_rates = []

    for i in range(5, -1, -1):
        month_start = timezone.now().replace(day=1) - timedelta(days=30 * i)
        month_name = month_start.strftime('%b')
        months.append(month_name)

        # Calculate attendance rate for the month
        month_attendance = Attendance.objects.filter(
            date__year=month_start.year,
            date__month=month_start.month
        )

        if month_attendance.exists():
            present_count = month_attendance.filter(status='present').count()
            total_count = month_attendance.count()
            rate = (present_count / total_count) * 100 if total_count > 0 else 0
            attendance_rates.append(round(rate, 1))
        else:
            attendance_rates.append(0)

    attendance_data = {
        'labels': months,
        'data': attendance_rates
    }

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'monthly_revenue': monthly_revenue,
        'recent_homework': recent_homework,
        'upcoming_exams': upcoming_exams,
        'todays_attendance': todays_attendance,
        'pending_payments': pending_payments,
        'performance_data': performance_data,
        'attendance_data': attendance_data,
        'current_date': timezone.now().strftime("%A, %B %d, %Y"),
        'user': request.user,
        'performance_data_json': json.dumps(performance_data),
        'attendance_data_json': json.dumps(attendance_data),
    }

    return render(request, 'admin/admin_dashboard.html', context)




# admin_student dashboard
class StudentListView(ListView):
    model = Student
    template_name = 'admin/admin_students.html'
    context_object_name = 'students'
    paginate_by = 10

    def get_queryset(self):
        queryset = Student.objects.select_related('user').all()

        # Filtering logic
        status_filter = self.request.GET.get('status')
        group_filter = self.request.GET.get('group')
        search_query = self.request.GET.get('search')

        if status_filter and status_filter != 'all':
            if status_filter == 'active':
                queryset = queryset.filter(user__is_active=True)
            elif status_filter == 'inactive':
                queryset = queryset.filter(user__is_active=False)

        if search_query:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

        return queryset.order_by('user__first_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Move all database queries inside this method
        total_groups = Group.objects.filter(status='active').count()
        total_students = Student.objects.count()
        active_students = Student.objects.filter(user__is_active=True).count()
        inactive_students = Student.objects.filter(user__is_active=False).count()

        context.update({
            'total_groups': total_groups,
            'total_students': total_students,
            'active_students': active_students,
            'inactive_students': inactive_students,
            'active_groups': 24,  # You'll need to implement group logic
            'average_attendance': 92,  # Implement your attendance logic
            'fee_completion': 87,  # Implement your payment logic
        })

        return context

class StudentCreateView(CreateView):
    model = User
    template_name = 'admin/student_form.html'
    fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'address']
    success_url = reverse_lazy('student_list')

    def form_valid(self, form):
        response = super().form_valid(form)

        # Create student profile
        student = Student.objects.create(user=self.object)

        messages.success(self.request, 'Student added successfully!')
        return response


class StudentUpdateView(UpdateView):
    model = User
    template_name = 'admin/student_form.html'
    fields = ['first_name', 'last_name', 'email', 'username', 'phone', 'address', 'is_active']
    success_url = reverse_lazy('student_list')

    def get_object(self):
        return get_object_or_404(User, pk=self.kwargs['pk'])

    def form_valid(self, form):
        messages.success(self.request, 'Student updated successfully!')
        return super().form_valid(form)


class StudentDetailView(DetailView):
    model = Student
    template_name = 'admin/student_detail.html'
    context_object_name = 'student'


class StudentDeleteView(DeleteView):
    model = Student
    template_name = 'admin/student_confirm_delete.html'
    success_url = reverse_lazy('student_list')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Student deleted successfully!')
        return super().delete(request, *args, **kwargs)


# API Views for dynamic data
def student_stats_api(request):
    """API endpoint for student statistics"""
    total_students = Student.objects.count()
    active_students = Student.objects.filter(user__is_active=True).count()

    # Calculate monthly growth (example)
    last_month = timezone.now() - timedelta(days=30)
    new_students_month = Student.objects.filter(enrollment_date__gte=last_month).count()

    data = {
        'total_students': total_students,
        'active_students': active_students,
        'new_students_month': new_students_month,
        'average_attendance': 92,
        'fee_completion': 87,
    }

    return JsonResponse(data)


def student_data_api(request):
    """API endpoint for student data (AJAX)"""
    students = Student.objects.select_related('user').all()

    student_list = []
    for student in students:
        student_list.append({
            'id': student.id,
            'name': f"{student.user.first_name} {student.user.last_name}",
            'email': student.user.email,
            'phone': student.user.phone,
            'enrollment_date': student.enrollment_date.strftime('%b %d, %Y'),
            'status': 'Active' if student.user.is_active else 'Inactive',
            'avatar_text': f"{student.user.first_name[0]}{student.user.last_name[0]}",
        })

    return JsonResponse({'students': student_list})




# admin_teacher

@login_required
def teachers_list(request):
    # Filtirlash va qidirish
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    subject_filter = request.GET.get('subject', 'all')
    total_groups = Group.objects.filter(status='active').count()
    teachers = Teacher.objects.select_related('user').all()
    if search_query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )

    if status_filter != 'all':
        if status_filter == 'active':
            teachers = teachers.filter(user__is_active=True)
        elif status_filter == 'inactive':
            teachers = teachers.filter(user__is_active=False)

    if subject_filter != 'all':
        teachers = teachers.filter(subjects__id=subject_filter)

    # Statistikalar
    total_teachers = Teacher.objects.count()
    active_teachers = Teacher.objects.filter(user__is_active=True).count()
    subjects_count = Subject.objects.count()

    # O'rtacha reyting (keyinroq qo'shishingiz mumkin)
    average_rating = 4.8

    context = {
        'total_groups': total_groups,
        'teachers': teachers,
        'subjects': Subject.objects.all(),
        'stats': {
            'total_teachers': total_teachers,
            'active_teachers': active_teachers,
            'subjects_count': subjects_count,
            'average_rating': average_rating,
        }
    }

    return render(request, 'admin/admin_teacher.html', context)


@login_required
def add_teacher(request):
    if request.method == 'POST':
        try:
            # User yaratish
            user = User.objects.create_user(
                username=request.POST.get('email'),
                email=request.POST.get('email'),
                password='temp_password123',  # Keyin o'zgartirish kerak
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                phone=request.POST.get('phone'),
                address=request.POST.get('address'),
                role='teacher'
            )

            # Teacher yaratish
            teacher = Teacher.objects.create(
                user=user,
                qualifications=request.POST.get('qualifications'),
                hire_date=request.POST.get('hire_date')
            )

            # Fanlarni qo'shish
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)

            # Statusni o'rnatish
            user.is_active = request.POST.get('status') == 'active'
            user.save()

            messages.success(request, 'Teacher added successfully!')
            return redirect('teachers_list')

        except Exception as e:
            messages.error(request, f'Error adding teacher: {str(e)}')

    return render(request, 'admin/add_teacher.html', {
        'subjects': Subject.objects.all()
    })


@login_required
def edit_teacher(request, teacher_id):
    teacher = get_object_or_404(Teacher, id=teacher_id)
    user = teacher.user

    if request.method == 'POST':
        try:
            # User ma'lumotlarini yangilash
            user.first_name = request.POST.get('first_name')
            user.last_name = request.POST.get('last_name')
            user.email = request.POST.get('email')
            user.phone = request.POST.get('phone')
            user.address = request.POST.get('address')
            user.is_active = request.POST.get('status') == 'active'
            user.save()

            # Teacher ma'lumotlarini yangilash
            teacher.qualifications = request.POST.get('qualifications')
            teacher.hire_date = request.POST.get('hire_date')
            teacher.save()

            # Fanlarni yangilash
            subject_ids = request.POST.getlist('subjects')
            teacher.subjects.set(subject_ids)

            messages.success(request, 'Teacher updated successfully!')
            return redirect('teachers_list')

        except Exception as e:
            messages.error(request, f'Error updating teacher: {str(e)}')

    return render(request, 'admin/edit_teacher.html', {
        'teacher': teacher,
        'subjects': Subject.objects.all()
    })


@login_required
def delete_teacher(request, teacher_id):
    if request.method == 'POST':
        try:
            teacher = get_object_or_404(Teacher, id=teacher_id)
            user = teacher.user
            teacher.delete()
            user.delete()

            messages.success(request, 'Teacher deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting teacher: {str(e)}')

    return redirect('teachers_list')

# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~# ~~~~~~~~~~~~~~~~~~~~~~~~~


from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Avg, Q
from education.models import Homework, Subject
from exams.models import Exam, Result
from groups.models import Group, Attendance, GroupMembership
from payments.models import Fee
from .decorators import teacher_required
from django.contrib.auth.decorators import login_required


@login_required
@teacher_required
def teacher_dashboard(request):
    # Get teacher profile
    teacher = get_object_or_404(Teacher, user=request.user)

    # Get current date info
    today = timezone.now().date()

    # Get teacher's active groups
    active_groups = Group.objects.filter(teacher=teacher, status='active')

    # Calculate statistics
    total_students = Student.objects.filter(
        groupmembership__group__in=active_groups
    ).distinct().count()

    active_classes_count = active_groups.count()

    # Pending assignments (homework due in future)
    pending_assignments = Homework.objects.filter(
        assigned_by=teacher,
        due_date__gte=timezone.now()
    ).count()

    # Average performance (average of all exam results for teacher's groups)
    average_performance = Result.objects.filter(
        exam__group__teacher=teacher
    ).aggregate(avg_score=Avg('score'))['avg_score'] or 0

    # Today's classes (groups with classes scheduled today)
    # Assuming schedule JSON has days of week - you might need to adjust this logic
    today_classes = []
    for group in active_groups:
        # Basic implementation - you might need to customize based on your schedule structure
        today_classes.append({
            'group': group,
            'subject': group.subject,
            'student_count': group.students.count()
        })

    # Recent homework (last 5 assignments)
    recent_homeworks = Homework.objects.filter(
        assigned_by=teacher
    ).order_by('-due_date')[:5]

    # Upcoming exams (next 5 exams)
    upcoming_exams = Exam.objects.filter(
        group__teacher=teacher,
        date__gte=timezone.now()
    ).order_by('date')[:5]

    context = {
        'teacher': teacher,
        'total_students': total_students,
        'active_classes_count': active_classes_count,
        'pending_assignments': pending_assignments,
        'average_performance': round(average_performance, 1),
        'today_classes': today_classes,
        'recent_homeworks': recent_homeworks,
        'upcoming_exams': upcoming_exams,
        'today': today,
    }

    return render(request, 'teacher/teacher_dashboard.html', context)


@login_required
@teacher_required
def teacher_classes(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    groups = Group.objects.filter(teacher=teacher)
    return render(request, 'teacher_classes.html', {'groups': groups})


@login_required
@teacher_required
def teacher_students(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    # Get students from teacher's groups
    students = Student.objects.filter(
        groupmembership__group__teacher=teacher
    ).distinct()
    return render(request, 'teacher_students.html', {'students': students})


@login_required
@teacher_required
def teacher_homework(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    homeworks = Homework.objects.filter(assigned_by=teacher)
    return render(request, 'teacher_homework.html', {'homeworks': homeworks})


@login_required
@teacher_required
def teacher_exams(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    exams = Exam.objects.filter(group__teacher=teacher)
    return render(request, 'teacher_exams.html', {'exams': exams})


@login_required
@teacher_required
def teacher_attendance(request):
    teacher = get_object_or_404(Teacher, user=request.user)
    # Get attendance records for teacher's groups
    attendance_records = Attendance.objects.filter(
        group__teacher=teacher
    ).order_by('-date')
    return render(request, 'teacher_attendance.html', {'attendance_records': attendance_records})


from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.db.models import Count, Q, Avg
from education.models import Homework, Subject
from exams.models import Exam, Result
from groups.models import Group, GroupMembership, Attendance
from payments.models import Fee
from .decorators import student_required
from django.http import JsonResponse


@student_required
def student_dashboard(request):
    # Get the student profile for the logged-in user
    student = get_object_or_404(Student, user=request.user)

    # Get student's groups
    student_groups = Group.objects.filter(
        groupmembership__student=student,
        status='active'
    ).distinct()

    # Calculate statistics
    # Pending homework (not due yet)
    pending_homework = Homework.objects.filter(
        assigned_to__in=student_groups,
        due_date__gt=timezone.now()
    ).count()

    # Upcoming exams
    upcoming_exams = Exam.objects.filter(
        group__in=student_groups,
        date__gt=timezone.now()
    ).count()

    # Pending payments
    pending_payments = Fee.objects.filter(
        student=student,
        status__in=['pending', 'overdue']
    ).count()

    # Attendance rate calculation
    total_attendance = Attendance.objects.filter(student=student).count()
    if total_attendance > 0:
        present_count = Attendance.objects.filter(student=student, status='present').count()
        attendance_rate = round((present_count / total_attendance) * 100, 1)
    else:
        attendance_rate = 0

    # Recent homework (last 10 assignments)
    recent_homework = Homework.objects.filter(
        assigned_to__in=student_groups
    ).order_by('-due_date')[:10]

    # Upcoming exams
    upcoming_exams_list = Exam.objects.filter(
        group__in=student_groups,
        date__gt=timezone.now()
    ).order_by('date')[:10]

    # Homework for homework tab
    homework_assignments = Homework.objects.filter(
        assigned_to__in=student_groups
    ).order_by('-due_date')

    # Attendance summary by subject
    attendance_summary = []
    for group in student_groups:
        total_classes = Attendance.objects.filter(
            student=student,
            group=group
        ).count()
        present_classes = Attendance.objects.filter(
            student=student,
            group=group,
            status='present'
        ).count()

        if total_classes > 0:
            attendance_percent = round((present_classes / total_classes) * 100, 1)
        else:
            attendance_percent = 0

        attendance_summary.append({
            'subject': group.subject.name,
            'group': group.name,
            'total_classes': total_classes,
            'present': present_classes,
            'absent': total_classes - present_classes,
            'attendance_percent': attendance_percent
        })

    # Recent attendance records
    recent_attendance = Attendance.objects.filter(
        student=student
    ).order_by('-date')[:10]

    # Exam results
    exam_results = Result.objects.filter(
        student=student
    ).order_by('-exam__date')

    # Payment history
    payment_history = Fee.objects.filter(
        student=student
    ).order_by('-due_date')

    context = {
        'student': student,
        'pending_homework': pending_homework,
        'upcoming_exams': upcoming_exams,
        'pending_payments': pending_payments,
        'attendance_rate': attendance_rate,
        'recent_homework': recent_homework,
        'upcoming_exams_list': upcoming_exams_list,
        'homework_assignments': homework_assignments,
        'attendance_summary': attendance_summary,
        'recent_attendance': recent_attendance,
        'exam_results': exam_results,
        'payment_history': payment_history,
        'student_groups': student_groups,
        'current_time': timezone.now(),
    }

    return render(request, 'student/student_dashboard.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from .decorators import admin_required
from .models import User, Teacher, Student, Parent
from .forms import AdminUserForm, AdminTeacherForm, AdminStudentForm, AdminParentForm
from django.utils import timezone
from datetime import timedelta
from .decorators import admin_required


# Add this view to users/views.py
@login_required
@admin_required
def admin_users_management(request):
    """Admin users management page"""
    # Get filter parameters
    search_query = request.GET.get('search', '')
    role_filter = request.GET.get('role', 'all')
    status_filter = request.GET.get('status', 'all')

    # Get all users
    users = User.objects.all().order_by('-date_joined')

    # Apply filters
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query)
        )

    if role_filter != 'all':
        users = users.filter(role=role_filter)

    if status_filter != 'all':
        users = users.filter(is_active=(status_filter == 'active'))

    # Get statistics
    total_users = User.objects.count()
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_parents = Parent.objects.count()

    context = {
        'users': users,
        'total_users': total_users,
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_parents': total_parents,
        'search_query': search_query,
        'role_filter': role_filter,
        'status_filter': status_filter,
    }

    return render(request, 'admin/admin_user.html', context)


@login_required
@admin_required
def admin_add_user(request):
    """Add new user from admin panel"""
    if request.method == 'POST':
        user_form = AdminUserForm(request.POST)

        if user_form.is_valid():
            try:
                # Create user
                user = user_form.save(commit=False)

                # Set password if provided
                password = user_form.cleaned_data.get('password')
                if password:
                    user.set_password(password)
                else:
                    user.set_password('defaultpassword123')  # Set a default password

                user.save()

                # Create profile based on role
                role = user.role
                if role == 'teacher':
                    teacher_form = AdminTeacherForm(request.POST)
                    if teacher_form.is_valid():
                        teacher = teacher_form.save(commit=False)
                        teacher.user = user
                        teacher.save()
                        # Handle subjects if needed
                elif role == 'student':
                    student_form = AdminStudentForm(request.POST)
                    if student_form.is_valid():
                        student = student_form.save(commit=False)
                        student.user = user
                        student.save()
                elif role == 'parent':
                    parent_form = AdminParentForm(request.POST)
                    if parent_form.is_valid():
                        parent = parent_form.save(commit=False)
                        parent.user = user
                        parent.save()
                        parent.students.set(parent_form.cleaned_data['students'])

                messages.success(request, f'User {user.get_full_name()} added successfully!')
                return redirect('admin_users_management')

            except Exception as e:
                messages.error(request, f'Error adding user: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        user_form = AdminUserForm()

    context = {
        'user_form': user_form,
        'teacher_form': AdminTeacherForm(),
        'student_form': AdminStudentForm(),
        'parent_form': AdminParentForm(),
        'students': Student.objects.all(),
    }

    return render(request, 'admin/add_user_modal.html', context)


@login_required
@admin_required
def admin_edit_user(request, user_id):
    """Edit existing user"""
    user = get_object_or_404(User, id=user_id)

    # Get the user's profile
    teacher_profile = None
    student_profile = None
    parent_profile = None

    if hasattr(user, 'teacher_profile'):
        teacher_profile = user.teacher_profile
    elif hasattr(user, 'student_profile'):
        student_profile = user.student_profile
    elif hasattr(user, 'parent_profile'):
        parent_profile = user.parent_profile

    if request.method == 'POST':
        user_form = AdminUserForm(request.POST, instance=user)

        if user_form.is_valid():
            try:
                user = user_form.save(commit=False)

                # Update password if provided
                password = user_form.cleaned_data.get('password')
                if password:
                    user.set_password(password)

                user.save()

                # Update profile based on role
                role = user.role
                if role == 'teacher' and teacher_profile:
                    teacher_form = AdminTeacherForm(request.POST, instance=teacher_profile)
                    if teacher_form.is_valid():
                        teacher_form.save()
                elif role == 'student' and student_profile:
                    student_form = AdminStudentForm(request.POST, instance=student_profile)
                    if student_form.is_valid():
                        student_form.save()
                elif role == 'parent' and parent_profile:
                    parent_form = AdminParentForm(request.POST, instance=parent_profile)
                    if parent_form.is_valid():
                        parent = parent_form.save()
                        parent.students.set(parent_form.cleaned_data['students'])

                messages.success(request, f'User {user.get_full_name()} updated successfully!')
                return redirect('admin_users_management')

            except Exception as e:
                messages.error(request, f'Error updating user: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        user_form = AdminUserForm(instance=user)

        # Initialize profile forms
        teacher_form = AdminTeacherForm(instance=teacher_profile) if teacher_profile else AdminTeacherForm()
        student_form = AdminStudentForm(instance=student_profile) if student_profile else AdminStudentForm()
        parent_form = AdminParentForm(instance=parent_profile) if parent_profile else AdminParentForm()

        if parent_profile:
            parent_form.fields['students'].initial = parent_profile.students.all()

    context = {
        'user_form': user_form,
        'teacher_form': teacher_form,
        'student_form': student_form,
        'parent_form': parent_form,
        'students': Student.objects.all(),
        'user': user,
    }

    return render(request, 'admin/edit_user_modal.html', context)


@login_required
@admin_required
def admin_delete_user(request, user_id):
    """Delete user"""
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        username = user.username

        try:
            user.delete()
            messages.success(request, f'User {username} deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting user: {str(e)}')

    return redirect('admin_users_management')


@login_required
@admin_required
def admin_users_stats_api(request):
    """API endpoint for user statistics"""
    stats = {
        'total_users': User.objects.count(),
        'total_students': Student.objects.count(),
        'total_teachers': Teacher.objects.count(),
        'total_parents': Parent.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'recent_users': User.objects.filter(date_joined__gte=timezone.now() - timedelta(days=30)).count(),
    }

    return JsonResponse(stats)