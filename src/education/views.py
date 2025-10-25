from django.contrib.auth.decorators import login_required

def admin_required(view_func):
    """Decorator to ensure user is admin"""

    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            return HttpResponseForbidden("You don't have permission to access this page.")
        return view_func(request, *args, **kwargs)

    return _wrapped_view


@login_required
@admin_required
def courses_dashboard(request):
    # Get filter parameters
    status_filter = request.GET.get('status', 'all')
    search_query = request.GET.get('search', '')

    # Start with all subjects
    subjects = Subject.objects.all()
    total_groups = Group.objects.filter(status='active').count()

    # Apply filters
    if status_filter != 'all':
        # Note: Subject model doesn't have status field, so we'll filter groups instead
        pass  # Remove this filter since Subject doesn't have status

    if search_query:
        subjects = subjects.filter(
            Q(name__icontains=search_query) |
            Q(code__icontains=search_query)
        )

    # Get statistics
    total_subjects = Subject.objects.count()
    active_courses = Subject.objects.count()  # Adjust this based on your business logic
    completed_courses = 0  # Adjust based on your business logic

    context = {
        'total_groups': total_groups,
        'subjects': subjects,
        'total_subjects': total_subjects,
        'active_groups': total_groups,  # Using actual group count
        'active_courses': active_courses,
        'completed_courses': completed_courses,
        'status_filter': status_filter,
        'search_query': search_query,
    }

    return render(request, 'admin/admin_courses.html', context)


@login_required
@admin_required
def add_subject(request):
    if request.method == 'POST':
        # Create a new subject with the form data
        name = request.POST.get('name')
        code = request.POST.get('code')
        description = request.POST.get('description', '')

        # Validate required fields
        if not name or not code:
            messages.error(request, 'Name and Code are required fields.')
            return redirect('education:courses_dashboard')

        # Check if code already exists
        if Subject.objects.filter(code=code).exists():
            messages.error(request, 'A subject with this code already exists.')
            return redirect('education:courses_dashboard')

        # Create the subject (only with fields that exist in model)
        Subject.objects.create(
            name=name,
            code=code,
            description=description,
        )

        messages.success(request, 'Subject added successfully!')
        return redirect('education:courses_dashboard')

    # If GET request, render the form
    return render(request, 'admin/subject_form.html')


@login_required
@admin_required
def edit_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        # Update the subject with the form data
        subject.name = request.POST.get('name')
        subject.code = request.POST.get('code')
        subject.description = request.POST.get('description', '')

        # Check if code already exists (excluding current subject)
        if Subject.objects.filter(code=subject.code).exclude(pk=pk).exists():
            messages.error(request, 'A subject with this code already exists.')
            return redirect('education:courses_dashboard')  # Fixed redirect URL

        subject.save()
        messages.success(request, 'Subject updated successfully!')
        return redirect('education:courses_dashboard')  # Fixed redirect URL

    # If GET request, show the form
    context = {
        'subject': subject,
        'edit_mode': True
    }
    return render(request, 'admin/subject_form.html', context)


@login_required
@admin_required
def view_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    # Debug output - remove this in production
    print(f"Subject: {subject.name}, {subject.code}, {subject.description}")

    return render(request, 'admin/subject_detail.html', {'subject': subject})


@login_required
@admin_required
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)

    if request.method == 'POST':
        subject.delete()
        messages.success(request, 'Subject deleted successfully!')
        return redirect('education:courses_dashboard')

    return render(request, 'admin/delete_confirmation.html', {'subject': subject})


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Q
from .models import Homework, Subject
from .forms import HomeworkFilterForm
from users.models import Student


@login_required
def student_homework(request):
    # Check if user is a student
    if not hasattr(request.user, 'student_profile'):
        return render(request, '403.html', status=403)

    student = request.user.student_profile
    now = timezone.now()

    # Get all homework for student's groups
    homework_queryset = Homework.objects.filter(
        assigned_to__students=student
    ).select_related('subject', 'assigned_by__user', 'assigned_to')

    # Initialize form with GET parameters
    form = HomeworkFilterForm(request.GET or None)

    # Get distinct subjects for filter choices
    student_subjects = Subject.objects.filter(
        group__students=student
    ).distinct()

    # Update form choices dynamically
    form.fields['subject'].choices = [('all', 'All Subjects')] + [
        (subject.id, subject.name) for subject in student_subjects
    ]

    # Apply filters
    if form.is_valid():
        subject_filter = form.cleaned_data.get('subject')
        status_filter = form.cleaned_data.get('status')
        sort_filter = form.cleaned_data.get('sort')

        # Filter by subject
        if subject_filter and subject_filter != 'all':
            homework_queryset = homework_queryset.filter(subject_id=subject_filter)

        # Filter by status
        if status_filter and status_filter != 'all':
            if status_filter == 'pending':
                homework_queryset = homework_queryset.filter(
                    due_date__gt=now
                ).exclude(
                    # Exclude homework that might be marked as completed via some other method
                    # You might want to add a submission model later
                    Q()  # Placeholder for completion logic
                )
            elif status_filter == 'completed':
                # You'll need to implement completion tracking
                # For now, this will return empty until you add submission model
                homework_queryset = homework_queryset.none()
            elif status_filter == 'overdue':
                homework_queryset = homework_queryset.filter(due_date__lt=now)

        # Apply sorting
        if sort_filter == 'due_date':
            homework_queryset = homework_queryset.order_by('due_date')
        elif sort_filter == 'subject':
            homework_queryset = homework_queryset.order_by('subject__name')
        elif sort_filter == 'created_at':
            homework_queryset = homework_queryset.order_by('-created_at')
    else:
        # Default sorting by due date
        homework_queryset = homework_queryset.order_by('due_date')

    # Prepare homework data for template
    homework_data = []
    for homework in homework_queryset:
        # Determine status
        if homework.due_date < now:
            status = 'overdue'
        else:
            status = 'pending'
        # Note: You'll need to add completion tracking separately

        homework_data.append({
            'id': homework.id,
            'title': homework.title,
            'subject': homework.subject.name,
            'subject_id': homework.subject.id,
            'assigned_by': homework.assigned_by.user.get_full_name() or homework.assigned_by.user.username,
            'due_date': homework.due_date,
            'description': homework.description,
            'status': status,
            'created_at': homework.created_at,
            'progress': 0,  # You'll need to implement progress tracking
        })

    # Calculate stats
    pending_count = len([h for h in homework_data if h['status'] == 'pending'])
    overdue_count = len([h for h in homework_data if h['status'] == 'overdue'])
    completed_count = 0  # You'll need to implement this

    context = {
        'homework_list': homework_data,
        'form': form,
        'pending_count': pending_count,
        'completed_count': completed_count,
        'overdue_count': overdue_count,
        'student_subjects': student_subjects,
    }

    return render(request, 'student/student_homework.html', context)


from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt


@require_POST
@csrf_exempt
@login_required
def mark_homework_done(request, pk):
    if not hasattr(request.user, 'student_profile'):
        return JsonResponse({'success': False, 'error': 'Not a student'})

    homework = get_object_or_404(Homework, pk=pk)
    student = request.user.student_profile

    # Check if student is in the group this homework was assigned to
    if not homework.assigned_to.students.filter(id=student.id).exists():
        return JsonResponse({'success': False, 'error': 'Not authorized'})

    # Here you would typically create a HomeworkSubmission record
    # For now, we'll just return success
    # HomeworkSubmission.objects.create(homework=homework, student=student, status='completed')

    return JsonResponse({'success': True})


# education/views.py (add these new views)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from .models import Subject, Homework
from groups.models import Group
from users.models import Teacher
import json

# ========== ADMIN HOMEWORK VIEWS ==========

@login_required
@admin_required
def admin_homework(request):
    """Admin view - see all homework in the system"""
    now = timezone.now()

    # Get all homework (admin sees everything)
    homework_queryset = Homework.objects.all().select_related(
        'subject', 'assigned_by__user', 'assigned_to'
    ).order_by('-created_at')

    # Get filter parameters
    subject_filter = request.GET.get('subject', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    # Apply filters
    if subject_filter:
        homework_queryset = homework_queryset.filter(subject_id=subject_filter)

    if status_filter:
        if status_filter == 'active':
            homework_queryset = homework_queryset.filter(due_date__gte=now)
        elif status_filter == 'completed':
            homework_queryset = homework_queryset.filter(due_date__lt=now)
        elif status_filter == 'upcoming':
            homework_queryset = homework_queryset.filter(due_date__gt=now)

    if search_query:
        homework_queryset = homework_queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Get all subjects and groups for filters (admin sees all)
    all_subjects = Subject.objects.all()
    all_groups = Group.objects.all()
    all_teachers = Teacher.objects.all()

    context = {
        'homework_list': homework_queryset,
        'all_subjects': all_subjects,
        'all_groups': all_groups,
        'all_teachers': all_teachers,
        'subject_filter': subject_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'now': now,
        'is_admin': True,  # Flag to identify admin view in template
    }

    return render(request, 'admin/admin_homework.html', context)


@login_required
@admin_required
def admin_add_homework(request):
    """Admin - add homework for any teacher/group"""
    if request.method == 'POST':
        try:
            # Get data from request
            title = request.POST.get('title')
            subject_id = request.POST.get('subject')
            assigned_by_id = request.POST.get('assigned_by')  # Admin can choose teacher
            assigned_to_id = request.POST.get('assigned_to')
            due_date_str = request.POST.get('due_date')
            description = request.POST.get('description', '')

            # Validate required fields
            if not all([title, subject_id, assigned_by_id, assigned_to_id, due_date_str]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})

            # Convert due_date string to datetime
            from django.utils.dateparse import parse_datetime
            due_date = parse_datetime(due_date_str)
            if not due_date:
                try:
                    from datetime import datetime
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid due date format'})

            # Create homework
            homework = Homework.objects.create(
                title=title,
                subject_id=subject_id,
                assigned_by_id=assigned_by_id,  # Use selected teacher
                assigned_to_id=assigned_to_id,
                due_date=due_date,
                description=description
            )

            return JsonResponse({'success': True, 'message': 'Homework added successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # If GET request, return method not allowed
    return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)


@login_required
@admin_required
def admin_edit_homework(request, pk):
    """Admin - edit any homework"""
    try:
        homework = Homework.objects.get(pk=pk)

        if request.method == 'GET':
            # Return homework data for editing
            homework_data = {
                'id': homework.id,
                'title': homework.title,
                'subject_id': homework.subject.id,
                'subject_name': homework.subject.name,
                'assigned_by_id': homework.assigned_by.id,
                'assigned_by_name': homework.assigned_by.user.get_full_name() or homework.assigned_by.user.username,
                'assigned_to_id': homework.assigned_to.id,
                'assigned_to_name': homework.assigned_to.name,
                'due_date': homework.due_date.strftime('%Y-%m-%dT%H:%M') if homework.due_date else None,
                'description': homework.description,
                'created_at': homework.created_at.strftime('%Y-%m-%d %H:%M:%S') if homework.created_at else None,
            }
            return JsonResponse({'success': True, 'homework': homework_data})

        elif request.method == 'POST':
            # Update homework
            homework.title = request.POST.get('title')
            homework.subject_id = request.POST.get('subject')
            homework.assigned_by_id = request.POST.get('assigned_by')  # Admin can change teacher
            homework.assigned_to_id = request.POST.get('assigned_to')

            # Convert due_date string to datetime
            due_date_str = request.POST.get('due_date')
            from django.utils.dateparse import parse_datetime
            due_date = parse_datetime(due_date_str)
            if due_date:
                homework.due_date = due_date

            homework.description = request.POST.get('description', '')
            homework.save()

            return JsonResponse({'success': True, 'message': 'Homework updated successfully!'})

    except Homework.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homework not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
@admin_required
def admin_delete_homework(request, pk):
    """Admin - delete any homework"""
    try:
        homework = Homework.objects.get(pk=pk)

        if request.method == 'POST':
            homework.delete()
            return JsonResponse({'success': True, 'message': 'Homework deleted successfully!'})
        else:
            return JsonResponse({'success': False, 'error': 'Only POST method allowed'}, status=405)

    except Homework.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homework not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

# ========== TEACHER HOMEWORK VIEWS ==========

@login_required
def teacher_homework(request):
    """Teacher view - see only their own homework"""
    # Check if user is a teacher
    if not hasattr(request.user, 'teacher_profile'):
        messages.error(request, "Access denied. Only teachers can view this page.")
        return redirect('education:courses_dashboard')

    teacher = request.user.teacher_profile
    now = timezone.now()

    # Get only homework assigned by this teacher
    homework_queryset = Homework.objects.filter(
        assigned_by=teacher
    ).select_related('subject', 'assigned_to').order_by('-created_at')

    # Get filter parameters
    subject_filter = request.GET.get('subject', '')
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')

    # Apply filters
    if subject_filter:
        homework_queryset = homework_queryset.filter(subject_id=subject_filter)

    if status_filter:
        if status_filter == 'active':
            homework_queryset = homework_queryset.filter(due_date__gte=now)
        elif status_filter == 'completed':
            homework_queryset = homework_queryset.filter(due_date__lt=now)
        elif status_filter == 'upcoming':
            homework_queryset = homework_queryset.filter(due_date__gt=now)

    if search_query:
        homework_queryset = homework_queryset.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # Get teacher's subjects and groups for filters
    teacher_subjects = Subject.objects.filter(
        Q(teacher=teacher) | Q(group__teacher=teacher)
    ).distinct()

    teacher_groups = Group.objects.filter(teacher=teacher)

    context = {
        'homework_list': homework_queryset,
        'teacher_subjects': teacher_subjects,
        'teacher_groups': teacher_groups,
        'subject_filter': subject_filter,
        'status_filter': status_filter,
        'search_query': search_query,
        'now': now,
        'is_teacher': True,  # Flag to identify teacher view in template
    }

    return render(request, 'teacher/teacher_homework.html', context)

@login_required
def teacher_add_homework(request):
    """Teacher - add homework only for their own groups"""
    if not hasattr(request.user, 'teacher_profile'):
        return JsonResponse({'success': False, 'error': 'Only teachers can add homework'}, status=403)

    if request.method == 'POST':
        try:
            teacher = request.user.teacher_profile

            # Get data from request
            title = request.POST.get('title')
            subject_id = request.POST.get('subject')
            assigned_to_id = request.POST.get('assigned_to')
            due_date_str = request.POST.get('due_date')
            description = request.POST.get('description', '')

            # Validate required fields
            if not all([title, subject_id, assigned_to_id, due_date_str]):
                return JsonResponse({'success': False, 'error': 'All fields are required'})

            # Check if the assigned group belongs to the teacher
            if not Group.objects.filter(id=assigned_to_id, teacher=teacher).exists():
                return JsonResponse({'success': False, 'error': 'You can only assign homework to your own groups'})

            # Convert due_date string to datetime
            from django.utils.dateparse import parse_datetime
            due_date = parse_datetime(due_date_str)
            if not due_date:
                try:
                    from datetime import datetime
                    due_date = datetime.strptime(due_date_str, '%Y-%m-%dT%H:%M')
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Invalid due date format'})

            # Create homework
            homework = Homework.objects.create(
                title=title,
                subject_id=subject_id,
                assigned_by=teacher,  # Always the current teacher
                assigned_to_id=assigned_to_id,
                due_date=due_date,
                description=description
            )

            return JsonResponse({'success': True, 'message': 'Homework added successfully!'})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def teacher_edit_homework(request, pk):
    """Teacher - edit only their own homework"""
    if not hasattr(request.user, 'teacher_profile'):
        return JsonResponse({'success': False, 'error': 'Only teachers can edit homework'}, status=403)

    try:
        homework = Homework.objects.get(pk=pk)
        teacher = request.user.teacher_profile

        # Check if the homework belongs to the current teacher
        if homework.assigned_by != teacher:
            return JsonResponse({'success': False, 'error': 'You can only edit your own homework'}, status=403)

        if request.method == 'GET':
            # Return homework data for editing
            homework_data = {
                'id': homework.id,
                'title': homework.title,
                'subject_id': homework.subject.id,
                'assigned_to_id': homework.assigned_to.id,
                'due_date': homework.due_date.strftime('%Y-%m-%dT%H:%M'),
                'description': homework.description,
            }
            return JsonResponse({'success': True, 'homework': homework_data})

        elif request.method == 'POST':
            # Check if the assigned group belongs to the teacher
            assigned_to_id = request.POST.get('assigned_to')
            if not Group.objects.filter(id=assigned_to_id, teacher=teacher).exists():
                return JsonResponse({'success': False, 'error': 'You can only assign homework to your own groups'})

            # Update homework
            homework.title = request.POST.get('title')
            homework.subject_id = request.POST.get('subject')
            homework.assigned_to_id = assigned_to_id

            # Convert due_date string to datetime
            due_date_str = request.POST.get('due_date')
            from django.utils.dateparse import parse_datetime
            due_date = parse_datetime(due_date_str)
            if due_date:
                homework.due_date = due_date

            homework.description = request.POST.get('description', '')
            homework.save()

            return JsonResponse({'success': True, 'message': 'Homework updated successfully!'})

    except Homework.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homework not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def teacher_delete_homework(request, pk):
    """Teacher - delete only their own homework"""
    if not hasattr(request.user, 'teacher_profile'):
        return JsonResponse({'success': False, 'error': 'Only teachers can delete homework'}, status=403)

    try:
        homework = Homework.objects.get(pk=pk)

        # Check if the homework belongs to the current teacher
        if homework.assigned_by != request.user.teacher_profile:
            return JsonResponse({'success': False, 'error': 'You can only delete your own homework'}, status=403)

        if request.method == 'POST':
            homework.delete()
            return JsonResponse({'success': True, 'message': 'Homework deleted successfully!'})

    except Homework.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Homework not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})