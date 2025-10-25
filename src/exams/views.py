from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render
from django.db.models import Q
from .models import Exam, Result
from .forms import ExamResultFilterForm
from users.models import User


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_exam_results(request):
    form = ExamResultFilterForm(request.GET or None)
    results = Result.objects.select_related(
        'exam', 'exam__subject', 'exam__group', 'student', 'student__user'
    ).all()

    if form.is_valid():
        subject = form.cleaned_data.get('subject')
        group = form.cleaned_data.get('group')
        exam = form.cleaned_data.get('exam')
        student = form.cleaned_data.get('student')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')

        if subject:
            results = results.filter(exam__subject=subject)
        if group:
            results = results.filter(exam__group=group)
        if exam:
            results = results.filter(exam=exam)
        if student:
            results = results.filter(student=student)
        if date_from:
            results = results.filter(exam__date__gte=date_from)
        if date_to:
            results = results.filter(exam__date__lte=date_to)

    # Order by exam date (newest first)
    results = results.order_by('-exam__date')

    # Prepare results with calculated percentages
    results_with_percentage = []
    for result in results:
        percentage = (result.score / result.exam.max_score) * 100 if result.exam.max_score > 0 else 0
        results_with_percentage.append({
            'result': result,
            'percentage': percentage
        })

    context = {
        'form': form,
        'results_with_percentage': results_with_percentage,
        'results_count': len(results_with_percentage),
    }

    return render(request, 'admin/admin_exam_result.html', context)


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.utils import timezone
from .models import Exam, Result
from .forms import ExamResultFilterForm, ExamForm
from education.models import Subject
from groups.models import Group
from users.models import User, Student, Teacher


def is_admin(user):
    return user.is_authenticated and user.role == 'admin'


@login_required
@user_passes_test(is_admin)
def admin_exam_management(request):
    # Get filter parameters
    subject_filter = request.GET.get('subject', '')
    group_filter = request.GET.get('group', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')

    # Get all exams with related data
    exams = Exam.objects.select_related('subject', 'group').prefetch_related('result_set').all()

    # Apply filters
    if subject_filter:
        exams = exams.filter(subject_id=subject_filter)
    if group_filter:
        exams = exams.filter(group_id=group_filter)
    if date_filter:
        exams = exams.filter(date__date=date_filter)

    # Separate upcoming and completed exams based on current time
    now = timezone.now()
    upcoming_exams = exams.filter(date__gt=now).order_by('date')
    completed_exams = exams.filter(date__lte=now).order_by('-date')

    # Calculate average scores for completed exams
    for exam in completed_exams:
        avg_result = exam.result_set.aggregate(avg_score=Avg('score'))
        exam.avg_score = avg_result['avg_score'] or 0
        exam.student_count = exam.result_set.count()

    # Get filter options
    subjects = Subject.objects.all()
    groups = Group.objects.all()

    context = {
        'upcoming_exams': upcoming_exams,
        'completed_exams': completed_exams,
        'subjects': subjects,
        'groups': groups,
        'current_filters': {
            'subject': subject_filter,
            'group': group_filter,
            'status': status_filter,
            'date': date_filter,
        }
    }

    return render(request, 'admin/admin_exam.html', context)


@login_required
@user_passes_test(is_admin)
def create_exam(request):
    if request.method == 'POST':
        form = ExamForm(request.POST)
        if form.is_valid():
            exam = form.save()
            messages.success(request, f'Exam "{exam.name}" created successfully!')
            return redirect('exams:admin_exam_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm()

    return render(request, 'admin/exam_form.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def edit_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        form = ExamForm(request.POST, instance=exam)
        if form.is_valid():
            form.save()
            messages.success(request, f'Exam "{exam.name}" updated successfully!')
            return redirect('exams:admin_exam_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ExamForm(instance=exam)

    return render(request, 'admin/exam_form.html', {'form': form, 'exam': exam})


@login_required
@user_passes_test(is_admin)
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        exam_name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{exam_name}" deleted successfully!')
        return redirect('exams:admin_exam_management')

    return render(request, 'admin/confirm_delete.html', {'exam': exam})


from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q, Avg, Count, Max
from django.contrib import messages
from django.utils import timezone
from .models import Exam, Result
from .forms import ExamResultFilterForm, ExamForm, StudentExamFilterForm
from education.models import Subject
from groups.models import Group
from users.models import User, Student, Teacher


def is_student(user):
    return user.is_authenticated and user.role == 'student'


@login_required
@user_passes_test(is_student)
def student_exam_results(request):
    # Get the student profile for the current user
    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        messages.error(request, "Student profile not found.")
        return redirect('users:dashboard')

    form = StudentExamFilterForm(request.GET or None)
    results = Result.objects.filter(student=student).select_related(
        'exam', 'exam__subject', 'exam__group'
    ).order_by('-exam__date')

    # Apply subject and date filters
    if form.is_valid():
        subject = form.cleaned_data.get('subject')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        status_filter = form.cleaned_data.get('status')

        if subject:
            results = results.filter(exam__subject=subject)
        if date_from:
            results = results.filter(exam__date__gte=date_from)
        if date_to:
            results = results.filter(exam__date__lte=date_to)

    # Convert to list for Python-based status filtering
    results_list = list(results)

    # Apply status filtering in Python
    if form.is_valid() and form.cleaned_data.get('status'):
        status_filter = form.cleaned_data.get('status')
        filtered_results = []
        for result in results_list:
            percentage = (result.score / result.exam.max_score) * 100
            if status_filter == 'passed' and percentage >= 50:
                filtered_results.append(result)
            elif status_filter == 'failed' and percentage < 50:
                filtered_results.append(result)
        results_list = filtered_results

    # Calculate statistics
    total_exams = len(results_list)
    passed_exams = 0
    overall_total_percentage = 0

    # Prepare results with calculated percentages and status
    results_with_data = []
    subject_scores = {}

    for result in results_list:
        percentage = (result.score / result.exam.max_score) * 100 if result.exam.max_score > 0 else 0
        status = 'passed' if percentage >= 50 else 'failed'

        if status == 'passed':
            passed_exams += 1

        overall_total_percentage += percentage

        # Track subject scores for best subject calculation
        subject_name = result.exam.subject.name
        if subject_name in subject_scores:
            subject_scores[subject_name].append(percentage)
        else:
            subject_scores[subject_name] = [percentage]

        results_with_data.append({
            'result': result,
            'percentage': round(percentage, 1),
            'status': status,
            'percentage_int': int(percentage)
        })

    # Calculate overall average
    overall_avg = overall_total_percentage / total_exams if total_exams > 0 else 0

    # Find best subject
    subject_avgs = {}
    for subject, scores in subject_scores.items():
        subject_avgs[subject] = sum(scores) / len(scores)

    best_subject = max(subject_avgs.items(), key=lambda x: x[1]) if subject_avgs else ("None", 0)

    # Subject performance for sidebar
    subject_performance = []
    for subject, avg_score in subject_avgs.items():
        subject_performance.append({
            'subject': Subject.objects.get(name=subject),  # Get subject object
            'avg_score': round(avg_score, 1),
            'color': get_subject_color(subject)
        })

    # Sort by average score (descending)
    subject_performance.sort(key=lambda x: x['avg_score'], reverse=True)

    context = {
        'form': form,
        'results_with_data': results_with_data,
        'student': student,
        'stats': {
            'overall_avg': round(overall_avg, 1),
            'best_subject': best_subject[0],
            'best_subject_score': round(best_subject[1], 1),
            'passed_exams': passed_exams,
            'total_exams': total_exams,
        },
        'subject_performance': subject_performance,
        'current_filters': request.GET,
    }

    return render(request, 'student/student_exam_results.html', context)


def get_subject_color(subject_name):
    """Assign consistent colors to subjects"""
    color_map = {
        'Mathematics': '#2563EB',
        'Physics': '#10B981',
        'Chemistry': '#8B5CF6',
        'Biology': '#F59E0B',
        'Computer Science': '#EF4444',
        'English': '#EC4899',
        'History': '#6B7280',
    }
    return color_map.get(subject_name, '#6B7280')


# exams/views.py (add these teacher views)
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.contrib import messages
from django.utils import timezone
from .models import Exam, Result
from .forms import TeacherExamForm, TeacherResultForm
from education.models import Subject
from groups.models import Group, GroupMembership
from users.models import User, Student, Teacher


def is_teacher(user):
    return user.is_authenticated and user.role == 'teacher'


@login_required
@user_passes_test(is_teacher)
def teacher_exam_management(request):
    # Get the teacher profile for current user
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('users:dashboard')

    # Get filter parameters
    subject_filter = request.GET.get('subject', '')
    group_filter = request.GET.get('group', '')
    status_filter = request.GET.get('status', '')
    search_term = request.GET.get('search', '')

    # Get exams only for groups taught by this teacher
    exams = Exam.objects.select_related('subject', 'group').prefetch_related('result_set').filter(
        group__teacher=teacher
    )

    # Apply filters
    if subject_filter:
        exams = exams.filter(subject_id=subject_filter)
    if group_filter:
        exams = exams.filter(group_id=group_filter)
    if search_term:
        exams = exams.filter(
            Q(name__icontains=search_term) |
            Q(subject__name__icontains=search_term)
        )

    # Separate upcoming and completed exams based on current time
    now = timezone.now()
    upcoming_exams = exams.filter(date__gt=now).order_by('date')
    completed_exams = exams.filter(date__lte=now).order_by('-date')
    all_exams = exams.order_by('-date')

    # Get filter options for this teacher only
    subjects = Subject.objects.filter(teacher=teacher).distinct()
    groups = Group.objects.filter(teacher=teacher)

    # Determine which tab is active
    active_tab = request.GET.get('tab', 'upcoming')
    if active_tab == 'completed':
        display_exams = completed_exams
    elif active_tab == 'all':
        display_exams = all_exams
    else:
        display_exams = upcoming_exams

    context = {
        'upcoming_exams': upcoming_exams,
        'completed_exams': completed_exams,
        'all_exams': all_exams,
        'display_exams': display_exams,
        'subjects': subjects,
        'groups': groups,
        'active_tab': active_tab,
        'current_filters': {
            'subject': subject_filter,
            'group': group_filter,
            'status': status_filter,
            'search': search_term,
        },
        'teacher': teacher,
    }

    return render(request, 'teacher/teacher_exam.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_create_exam(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('exams:teacher_exam_management')

    if request.method == 'POST':
        form = TeacherExamForm(request.POST, teacher=teacher)
        if form.is_valid():
            exam = form.save()
            messages.success(request, f'Exam "{exam.name}" created successfully!')
            return redirect('exams:teacher_exam_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherExamForm(teacher=teacher)

    return render(request, 'teacher/exam_form.html', {'form': form})


@login_required
@user_passes_test(is_teacher)
def teacher_edit_exam(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('exams:teacher_exam_management')

    exam = get_object_or_404(Exam, id=exam_id, group__teacher=teacher)

    if request.method == 'POST':
        form = TeacherExamForm(request.POST, instance=exam, teacher=teacher)
        if form.is_valid():
            form.save()
            messages.success(request, f'Exam "{exam.name}" updated successfully!')
            return redirect('exams:teacher_exam_management')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = TeacherExamForm(instance=exam, teacher=teacher)

    return render(request, 'teacher/exam_form.html', {'form': form, 'exam': exam})


@login_required
@user_passes_test(is_teacher)
def teacher_delete_exam(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('exams:teacher_exam_management')

    exam = get_object_or_404(Exam, id=exam_id, group__teacher=teacher)

    if request.method == 'POST':
        exam_name = exam.name
        exam.delete()
        messages.success(request, f'Exam "{exam_name}" deleted successfully!')
        return redirect('exams:teacher_exam_management')

    return render(request, 'teacher/confirm_delete.html', {'exam': exam})


@login_required
@user_passes_test(is_teacher)
def teacher_exam_results(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('exams:teacher_exam_management')

    exam = get_object_or_404(Exam, id=exam_id, group__teacher=teacher)

    # Get students in this group
    students = Student.objects.filter(
        groupmembership__group=exam.group
    ).select_related('user')

    # Get existing results
    existing_results = {result.student_id: result for result in exam.result_set.all()}

    student_results = []
    for student in students:
        result = existing_results.get(student.id)
        student_results.append({
            'student': student,
            'result': result,
            'score': result.score if result else None,
            'remarks': result.remarks if result else '',
            'percentage': (result.score / exam.max_score * 100) if result and exam.max_score > 0 else 0
        })

    context = {
        'exam': exam,
        'student_results': student_results,
        'teacher': teacher,
    }

    return render(request, 'teacher/exam_results.html', context)


@login_required
@user_passes_test(is_teacher)
def teacher_save_results(request, exam_id):
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher profile not found.")
        return redirect('exams:teacher_exam_management')

    exam = get_object_or_404(Exam, id=exam_id, group__teacher=teacher)

    if request.method == 'POST':
        try:
            for key, value in request.POST.items():
                if key.startswith('score_'):
                    student_id = int(key.replace('score_', ''))
                    score = int(value) if value else 0
                    remarks = request.POST.get(f'remarks_{student_id}', '')

                    # Validate score
                    if score > exam.max_score:
                        messages.error(request, f'Score {score} exceeds maximum score {exam.max_score}')
                        return redirect('exams:teacher_exam_results', exam_id=exam_id)

                    # Create or update result
                    result, created = Result.objects.update_or_create(
                        exam=exam,
                        student_id=student_id,
                        defaults={
                            'score': score,
                            'remarks': remarks
                        }
                    )

            messages.success(request, f'Results for "{exam.name}" saved successfully!')
            return redirect('exams:teacher_exam_results', exam_id=exam_id)

        except Exception as e:
            messages.error(request, f'Error saving results: {str(e)}')
            return redirect('exams:teacher_exam_results', exam_id=exam_id)

    messages.error(request, 'Invalid request method.')
    return redirect('exams:teacher_exam_results', exam_id=exam_id)