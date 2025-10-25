from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from .models import Group, GroupMembership, Attendance
from users.models import Teacher, Student
from education.models import Subject
import json


def groups_list(request):
    # Statistik ma'lumotlar
    total_groups = Group.objects.count()
    total_students = Student.objects.count()

    # O'rtacha davomatni hisoblash (soddalashtirilgan)
    attendance_records = Attendance.objects.all()
    avg_attendance = 0
    if attendance_records.exists():
        present_count = attendance_records.filter(status='present').count()
        avg_attendance = round((present_count / attendance_records.count()) * 100)

    active_teachers = Teacher.objects.filter(user__is_active=True).count()

    # Guruhlarni olish
    groups = Group.objects.select_related('teacher', 'subject').prefetch_related('students').all()

    # Filtrlash
    status_filter = request.GET.get('status', 'all')
    subject_filter = request.GET.get('subject', 'all')
    teacher_filter = request.GET.get('teacher', 'all')
    search_query = request.GET.get('search', '')

    if search_query:
        groups = groups.filter(name__icontains=search_query)

    if status_filter != 'all':
        # Bu yerda status maydoni yo'q, shuning uchun faqat active/inactive ni ko'rsatish
        # Siz modelga status maydonini qo'shishingiz kerak bo'ladi
        pass

    if subject_filter != 'all':
        groups = groups.filter(subject__name=subject_filter)

    if teacher_filter != 'all':
        groups = groups.filter(teacher__user__first_name=teacher_filter)

    # Har bir guruh uchun davomatni hisoblash
    groups_with_attendance = []
    for group in groups:
        group_attendance = Attendance.objects.filter(group=group)
        attendance_rate = 0
        if group_attendance.exists():
            present_count = group_attendance.filter(status='present').count()
            attendance_rate = round((present_count / group_attendance.count()) * 100)

        groups_with_attendance.append({
            'group': group,
            'attendance_rate': attendance_rate,
            'student_count': group.students.count()
        })

    context = {
        'total_groups': total_groups,
        'total_students': total_students,
        'avg_attendance': avg_attendance,
        'active_teachers': active_teachers,
        'groups_with_attendance': groups_with_attendance,
        'subjects': Subject.objects.all(),
        'teachers': Teacher.objects.select_related('user').all(),
        'status_filter': status_filter,
        'subject_filter': subject_filter,
        'teacher_filter': teacher_filter,
        'search_query': search_query,
    }

    return render(request, 'admin/admin_group.html', context)


def add_group(request):
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            subject_id = request.POST.get('subject')
            teacher_id = request.POST.get('teacher')
            schedule_data = request.POST.get('schedule')
            status = request.POST.get('status', 'active')

            subject = get_object_or_404(Subject, id=subject_id)
            teacher = get_object_or_404(Teacher, id=teacher_id)

            # Schedule JSON formatiga o'tkazish
            schedule = {"schedule": schedule_data}

            group = Group.objects.create(
                name=name,
                subject=subject,
                teacher=teacher,
                schedule=schedule
            )

            messages.success(request, 'Guruh muvaffaqiyatli qo\'shildi!')
            return redirect('groups_list')

        except Exception as e:
            messages.error(request, f'Xatolik yuz berdi: {str(e)}')
            return redirect('groups_list')

    return redirect('groups_list')


def edit_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        try:
            group.name = request.POST.get('name')
            subject_id = request.POST.get('subject')
            teacher_id = request.POST.get('teacher')
            schedule_data = request.POST.get('schedule')

            group.subject = get_object_or_404(Subject, id=subject_id)
            group.teacher = get_object_or_404(Teacher, id=teacher_id)
            group.schedule = {"schedule": schedule_data}

            group.save()

            messages.success(request, 'Guruh muvaffaqiyatli yangilandi!')
            return redirect('groups_list')

        except Exception as e:
            messages.error(request, f'Xatolik yuz berdi: {str(e)}')

    return redirect('groups_list')


def delete_group(request, group_id):
    group = get_object_or_404(Group, id=group_id)

    if request.method == 'POST':
        group.delete()
        messages.success(request, 'Guruh muvaffaqiyatli o\'chirildi!')

    return redirect('groups_list')


def group_detail(request, group_id):
    group = get_object_or_404(Group, id=group_id)
    students = group.students.all()
    attendance_records = Attendance.objects.filter(group=group)

    context = {
        'group': group,
        'students': students,
        'attendance_records': attendance_records,
    }

    return render(request, 'admin/group_detail.html', context)














#Teacher Attandance
# attendance/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Attendance, Group, GroupMembership
from users.models import Student, Teacher
import csv
from datetime import datetime


@login_required
def attendance_list(request):
    # Filtrlarni olish
    group_filter = request.GET.get('group', '')
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')

    # Attendance obyektlarini olish
    attendances = Attendance.objects.all().select_related('student', 'group', 'recorded_by')

    # Filtrlash
    if group_filter:
        attendances = attendances.filter(group_id=group_filter)
    if date_filter:
        attendances = attendances.filter(date=date_filter)
    if status_filter:
        attendances = attendances.filter(status=status_filter)

    # Guruhlarni olish (filter uchun)
    groups = Group.objects.all()

    context = {
        'attendances': attendances,
        'groups': groups,
        'group_filter': group_filter,
        'date_filter': date_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin/admin_attendance.html', context)

def get_student_groups(request, student_id):
    try:
        memberships = GroupMembership.objects.filter(student_id=student_id)
        groups = [{'id': m.group.id, 'name': m.group.name} for m in memberships]

        return JsonResponse({'success': True, 'groups': groups})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})



@login_required
def attendance_add(request):
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            group_id = request.POST.get('group')
            date = request.POST.get('date')
            status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            # Hozirgi foydalanuvchi (admin yoki teacher bo'lishi mumkin)
            recorded_by = request.user

            attendance = Attendance(
                student_id=student_id,
                group_id=group_id,
                date=date,
                status=status,
                recorded_by=recorded_by,
                notes=notes
            )
            attendance.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # GET so'rovida student va group ma'lumotlarini yuborish
    students = Student.objects.all()
    groups = Group.objects.all()

    return JsonResponse({
        'students': [{'id': s.id, 'name': str(s)} for s in students],
        'groups': [{'id': g.id, 'name': g.name} for g in groups]
    })


@login_required
def attendance_edit(request, pk):
    attendance = get_object_or_404(Attendance, pk=pk)

    if request.method == 'POST':
        try:
            # POST ma'lumotlarini olish
            student_id = request.POST.get('student')
            group_id = request.POST.get('group')
            date_str = request.POST.get('date')
            status = request.POST.get('status')
            notes = request.POST.get('notes', '')

            # ForeignKeylarni yangilash
            if student_id:
                attendance.student = Student.objects.get(pk=student_id)
            if group_id:
                attendance.group = Group.objects.get(pk=group_id)

            # Sana string → date
            if date_str:
                attendance.date = datetime.strptime(date_str, "%Y-%m-%d").date()

            attendance.status = status
            attendance.notes = notes
            attendance.save()

            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # GET so'rov → ma'lumotlarni JSON qaytarish
    students = Student.objects.all()
    groups = Group.objects.all()

    return JsonResponse({
        'attendance': {
            'id': attendance.id,
            'student_id': attendance.student.id,
            'group_id': attendance.group.id,
            'date': attendance.date.strftime('%Y-%m-%d'),
            'status': attendance.status,
            'notes': attendance.notes or ""
        },
        'students': [{'id': s.id, 'name': str(s)} for s in students],
        'groups': [{'id': g.id, 'name': g.name} for g in groups]
    })

@login_required
def attendance_delete(request, pk):
    if request.method == 'POST':
        attendance = get_object_or_404(Attendance, pk=pk)
        attendance.delete()
        return JsonResponse({'success': True})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def attendance_export(request):
    # Filtrlarni olish
    group_filter = request.GET.get('group', '')
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')

    attendances = Attendance.objects.all().select_related('student', 'group', 'recorded_by')

    if group_filter:
        attendances = attendances.filter(group_id=group_filter)
    if date_filter:
        attendances = attendances.filter(date=date_filter)
    if status_filter:
        attendances = attendances.filter(status=status_filter)

    response = HttpResponse(content_type='text/csv')
    response[
        'Content-Disposition'] = f'attachment; filename="attendance_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Student', 'Group', 'Date', 'Status', 'Recorded By', 'Notes'])

    for attendance in attendances:
        writer.writerow([
            str(attendance.student),
            attendance.group.name,
            attendance.date,
            attendance.get_status_display(),
            str(attendance.recorded_by),
            attendance.notes
        ])

    return response


# teacher attendance
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import Group, Attendance, GroupMembership
from users.models import Teacher, Student
import json


def is_teacher(user):
    return user.is_authenticated and hasattr(user, 'teacher_profile')


@login_required
@user_passes_test(is_teacher, login_url='/login/')
def attendance_view(request):
    teacher = request.user.teacher_profile
    teacher_groups = Group.objects.filter(teacher=teacher)

    # Get filter parameters
    group_filter = request.GET.get('group_filter', '')
    date_from = request.GET.get('date_from', (timezone.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', timezone.now().strftime('%Y-%m-%d'))
    status_filter = request.GET.get('status_filter', '')

    # Filter attendance records
    attendance_records = Attendance.objects.filter(
        group__teacher=teacher,
        date__range=[date_from, date_to]
    ).select_related('student__user', 'group', 'recorded_by')

    if group_filter:
        attendance_records = attendance_records.filter(group_id=group_filter)

    if status_filter:
        attendance_records = attendance_records.filter(status=status_filter)

    # Calculate statistics for current month
    current_month = timezone.now().month
    current_year = timezone.now().year

    monthly_attendance = Attendance.objects.filter(
        group__teacher=teacher,
        date__year=current_year,
        date__month=current_month
    )

    present_count = monthly_attendance.filter(status='present').count()
    absent_count = monthly_attendance.filter(status='absent').count()
    late_count = monthly_attendance.filter(status='late').count()
    total_monthly = monthly_attendance.count()

    overall_attendance_rate = round((present_count / total_monthly * 100) if total_monthly > 0 else 0, 1)
    absences_this_month = absent_count
    late_arrivals = late_count

    # Get total students across all teacher's groups
    total_students = Student.objects.filter(
        groupmembership__group__teacher=teacher
    ).distinct().count()

    context = {
        'teacher_groups': teacher_groups,
        'attendance_records': attendance_records,
        'overall_attendance_rate': overall_attendance_rate,
        'absences_this_month': absences_this_month,
        'late_arrivals': late_arrivals,
        'total_students': total_students,
        'today': timezone.now().date().isoformat(),
        'selected_group': group_filter,
        'date_from': date_from,
        'date_to': date_to,
        'status_filter': status_filter,
    }

    return render(request, 'teacher/teacher_attendance.html', context)


@login_required
@user_passes_test(is_teacher)
def get_students_by_group(request):
    group_id = request.GET.get('group_id')
    if group_id:
        try:
            students = Student.objects.filter(
                groupmembership__group_id=group_id
            ).select_related('user')

            student_list = []
            for student in students:
                user = student.user
                # Get initials safely
                first_initial = user.first_name[0] if user.first_name and len(user.first_name) > 0 else ''
                last_initial = user.last_name[0] if user.last_name and len(user.last_name) > 0 else ''
                initials = f"{first_initial}{last_initial}".upper() if first_initial or last_initial else 'ST'

                # Get full name
                full_name = user.get_full_name()
                if not full_name:
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if not full_name:
                    full_name = user.username or f"Student {student.id}"

                student_list.append({
                    'id': student.id,
                    'name': full_name,
                    'initials': initials,
                })

            return JsonResponse({'success': True, 'students': student_list})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'No group ID provided'})


@login_required
@user_passes_test(is_teacher)
def save_attendance(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            group_id = data.get('group_id')
            date = data.get('date')
            attendance_data = data.get('attendance', {})

            group = Group.objects.get(id=group_id, teacher=request.user.teacher_profile)

            saved_count = 0
            errors = []

            for student_id, status in attendance_data.items():
                try:
                    student = Student.objects.get(id=student_id)

                    # Check if student is in the group
                    if not GroupMembership.objects.filter(group=group, student=student).exists():
                        errors.append(f"Student {student_id} is not in this group")
                        continue

                    # Create or update attendance
                    attendance, created = Attendance.objects.update_or_create(
                        student=student,
                        group=group,
                        date=date,
                        defaults={
                            'status': status,
                            'recorded_by': request.user
                        }
                    )
                    saved_count += 1

                except Student.DoesNotExist:
                    errors.append(f"Student {student_id} not found")
                except Exception as e:
                    errors.append(f"Error saving attendance for student {student_id}: {str(e)}")

            if errors:
                return JsonResponse({
                    'success': True,
                    'message': f'Attendance saved for {saved_count} students, but with some errors',
                    'errors': errors
                })
            else:
                return JsonResponse({
                    'success': True,
                    'message': f'Attendance successfully saved for {saved_count} students'
                })

        except Group.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Group not found or access denied'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# Teacher group
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime
from .models import Group, GroupMembership, Attendance
from education.models import Subject
from users.models import Teacher, Student


@login_required
def teacher_groups(request):
    # Foydalanuvchi teacher ekanligini tekshirish
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        # Agar teacher bo'lmasa, boshqa sahifaga yo'naltirish
        return redirect('dashboard')

    # Filtrlash parametrlari
    subject_filter = request.GET.get('subject', '')
    status_filter = request.GET.get('status', '')

    # Teacherning guruhlarini olish
    groups = Group.objects.filter(teacher=teacher)

    # Filtrlash
    if subject_filter:
        groups = groups.filter(subject_id=subject_filter)

    if status_filter:
        groups = groups.filter(status=status_filter)

    # Statistik ma'lumotlar
    total_groups = groups.count()
    total_students = GroupMembership.objects.filter(group__in=groups).values('student').distinct().count()

    # Vazifalar va imtihonlar statistikasi (soddalashtirilgan)
    pending_assignments = 12  # Static ma'lumot, keyin real ma'lumot bilan almashtirish mumkin
    upcoming_exams = 3  # Static ma'lumot

    # Barcha fanlar (filter uchun)
    subjects = Subject.objects.all()

    context = {
        'teacher': teacher,
        'groups': groups,
        'subjects': subjects,
        'total_groups': total_groups,
        'total_students': total_students,
        'pending_assignments': pending_assignments,
        'upcoming_exams': upcoming_exams,
        'selected_subject': subject_filter,
        'selected_status': status_filter,
    }

    return render(request, 'teacher/teacher_groups.html', context)


@login_required
def add_group(request):
    if request.method == 'POST':
        # Foydalanuvchi teacher ekanligini tekshirish
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Only teachers can create groups'})

        name = request.POST.get('name')
        subject_id = request.POST.get('subject')
        schedule = request.POST.get('schedule')

        if not name or not subject_id:
            return JsonResponse({'success': False, 'error': 'Name and subject are required'})

        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid subject'})

        # Yangi guruh yaratish
        group = Group.objects.create(
            name=name,
            subject=subject,
            teacher=teacher,
            schedule={'schedule_text': schedule},  # Soddalashtirilgan JSON
            status='active'
        )

        return JsonResponse({'success': True, 'group_id': group.id})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def group_detail(request, group_id):
    # Foydalanuvchi teacher ekanligini tekshirish
    try:
        teacher = Teacher.objects.get(user=request.user)
    except Teacher.DoesNotExist:
        return redirect('teacher_groups')

    # Guruhni olish (faqat teacherning o'zi ko'ra olishi uchun)
    group = get_object_or_404(Group, id=group_id, teacher=teacher)

    # Guruh a'zolari
    members = GroupMembership.objects.filter(group=group).select_related('student')

    # Davomat ma'lumotlari (oxirgi 7 kun)
    today = timezone.now().date()
    week_ago = today - timezone.timedelta(days=7)
    attendance = Attendance.objects.filter(
        group=group,
        date__gte=week_ago
    ).order_by('-date')

    context = {
        'group': group,
        'members': members,
        'attendance': attendance,
    }

    return render(request, 'groups/group_detail.html', context)


@login_required
def record_attendance(request, group_id):
    if request.method == 'POST':
        # Foydalanuvchi teacher ekanligini tekshirish
        try:
            teacher = Teacher.objects.get(user=request.user)
        except Teacher.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Only teachers can record attendance'})

        # Guruhni tekshirish
        group = get_object_or_404(Group, id=group_id, teacher=teacher)

        date_str = request.POST.get('date')
        student_id = request.POST.get('student')
        status = request.POST.get('status')
        notes = request.POST.get('notes', '')

        if not date_str or not student_id or not status:
            return JsonResponse({'success': False, 'error': 'Date, student and status are required'})

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
            student = Student.objects.get(id=student_id)
        except (ValueError, Student.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Invalid date or student'})

        # Student guruh a'zosi ekanligini tekshirish
        if not GroupMembership.objects.filter(group=group, student=student).exists():
            return JsonResponse({'success': False, 'error': 'Student is not a member of this group'})

        # Davomatni yaratish yoki yangilash
        attendance, created = Attendance.objects.update_or_create(
            student=student,
            group=group,
            date=date,
            defaults={
                'status': status,
                'notes': notes,
                'recorded_by': request.user
            }
        )

        return JsonResponse({'success': True, 'created': created})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})






# teacher group membership
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Group, GroupMembership, Attendance
from users.models import Student, Teacher
from education.models import Subject


@login_required
def group_detail(request, group_id):
    # Guruhni olish
    group = get_object_or_404(Group, id=group_id)

    # Foydalanuvchi teacher ekanligini tekshirish
    try:
        teacher = Teacher.objects.get(user=request.user)
        # Faqat o'z guruhini ko'ra olishi uchun
        if group.teacher != teacher:
            return redirect('groups:teacher_groups')
    except Teacher.DoesNotExist:
        # Admin yoki boshqa foydalanuvchilar barcha guruhlarni ko'ra oladi
        pass

    # Guruh a'zolari
    members = GroupMembership.objects.filter(group=group).select_related('student')

    # Davomat statistikasi
    today = timezone.now().date()
    last_30_days = today - timedelta(days=30)

    attendance_stats = Attendance.objects.filter(
        group=group,
        date__gte=last_30_days
    ).aggregate(
        total=Count('id'),
        present=Count('id', filter=Q(status='present')),
        absent=Count('id', filter=Q(status='absent')),
        late=Count('id', filter=Q(status='late')),
        excused=Count('id', filter=Q(status='excused'))
    )

    # Har bir talaba uchun statistikalar
    for member in members:
        student_attendance = Attendance.objects.filter(
            student=member.student,
            group=group,
            date__gte=last_30_days
        ).aggregate(
            total=Count('id'),
            present=Count('id', filter=Q(status='present')),
            late=Count('id', filter=Q(status='late'))
        )

        total_classes = student_attendance['total'] or 1
        present_classes = student_attendance['present'] or 0
        late_classes = student_attendance['late'] or 0

        # Davomat foizi (kechikishlar yarim hisoblanadi)
        member.attendance_percentage = round(
            (present_classes + (late_classes * 0.5)) / total_classes * 100, 1
        ) if total_classes > 0 else 0

        # O'rtacha ball (soddalashtirilgan)
        member.average_score = 85 + (member.student.id % 15)  # Tasodifiy qiymat

    # Umumiy statistikalar
    total_students = members.count()

    if attendance_stats['total'] > 0:
        overall_attendance = round(
            (attendance_stats['present'] + (attendance_stats['late'] * 0.5)) /
            attendance_stats['total'] * 100, 1
        )
    else:
        overall_attendance = 0

    overall_average_score = round(
        sum(member.average_score for member in members) / total_students, 1
    ) if total_students > 0 else 0

    # Qidiruv funksiyasi
    search_query = request.GET.get('search', '')
    if search_query:
        members = members.filter(
            Q(student__user__first_name__icontains=search_query) |
            Q(student__user__last_name__icontains=search_query) |
            Q(student__user__email__icontains=search_query)
        )

    context = {
        'group': group,
        'members': members,
        'total_students': total_students,
        'overall_attendance': overall_attendance,
        'overall_average_score': overall_average_score,
        'attendance_stats': attendance_stats,
        'search_query': search_query,
    }

    return render(request, 'teacher/teacher_group_detail.html', context)


@login_required
def add_student_to_group(request, group_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        student_id = request.POST.get('student_id')

        try:
            student = Student.objects.get(id=student_id)

            # Talaba allaqachon guruhda borligini tekshirish
            if GroupMembership.objects.filter(group=group, student=student).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Student is already in this group'
                })

            # Talabani guruhga qo'shish
            GroupMembership.objects.create(
                group=group,
                student=student,
                joined_date=timezone.now().date()
            )

            return JsonResponse({'success': True})

        except Student.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Student not found'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


@login_required
def remove_student_from_group(request, group_id, student_id):
    if request.method == 'POST':
        group = get_object_or_404(Group, id=group_id)
        student = get_object_or_404(Student, id=student_id)

        # Talabani guruhdan olib tashlash
        membership = GroupMembership.objects.filter(group=group, student=student)
        if membership.exists():
            membership.delete()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'success': False, 'error': 'Student not found in group'})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})


# In views.py - Update the get_available_students function

@login_required
@login_required
def get_available_students(request, group_id):
    """Get students not currently in this group with search functionality"""
    try:
        print(f"Getting available students for group {group_id}")  # Debug

        group = get_object_or_404(Group, id=group_id)

        # Get search query
        search_query = request.GET.get('search', '')
        print(f"Search query: {search_query}")  # Debug

        # Get students who are NOT in this group
        current_member_ids = GroupMembership.objects.filter(
            group=group
        ).values_list('student_id', flat=True)

        print(f"Current member IDs: {list(current_member_ids)}")  # Debug

        # Get all students
        available_students = Student.objects.all().select_related('user')

        # Exclude current members
        available_students = available_students.exclude(id__in=current_member_ids)

        print(f"Total available students before search: {available_students.count()}")  # Debug

        # Apply search filter if provided
        if search_query:
            available_students = available_students.filter(
                Q(user__first_name__icontains=search_query) |
                Q(user__last_name__icontains=search_query) |
                Q(user__email__icontains=search_query) |
                Q(user__username__icontains=search_query)
            )

        students_data = []
        for student in available_students:
            try:
                user = student.user

                # Get initials safely
                first_initial = user.first_name[0] if user.first_name and len(user.first_name) > 0 else ''
                last_initial = user.last_name[0] if user.last_name and len(user.last_name) > 0 else ''
                initials = f"{first_initial}{last_initial}".upper() if first_initial or last_initial else 'ST'

                # Get full name
                full_name = user.get_full_name()
                if not full_name:
                    full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if not full_name:
                    full_name = user.username or f"Student {student.id}"

                students_data.append({
                    'id': student.id,
                    'name': full_name,
                    'email': user.email or 'No email',
                    'initials': initials,
                })
            except Exception as e:
                print(f"Error processing student {student.id}: {e}")
                continue

        print(f"Found {len(students_data)} available students")  # Debug

        return JsonResponse({
            'success': True,
            'students': students_data,
            'count': len(students_data)
        })

    except Exception as e:
        print(f"Error in get_available_students: {e}")  # Debug
        import traceback
        traceback.print_exc()  # Print full traceback
        return JsonResponse({
            'success': False,
            'error': str(e),
            'students': []
        }, status=500)


def available_students_search(request, group_id):
    """Search for available students to add to a group"""
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        search_term = request.GET.get('search', '')

        try:
            # 1. Get the group
            group = get_object_or_404(Group, id=group_id)

            # 2. Get current student IDs in this group
            current_student_ids = GroupMembership.objects.filter(
                group=group
            ).values_list('student_id', flat=True)

            # 3. Search for students NOT in this group
            students = Student.objects.filter(
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term) |
                Q(user__email__icontains=search_term)
            ).exclude(id__in=current_student_ids).select_related('user')[:10]

            # 4. Format results
            results = []
            for student in students:
                user = student.user
                results.append({
                    'id': student.id,
                    'name': user.get_full_name() or f"{user.first_name} {user.last_name}".strip() or user.username,
                    'email': user.email,
                    'initials': f"{user.first_name[0] if user.first_name else ''}{user.last_name[0] if user.last_name else ''}".upper() or 'ST'
                })

            return JsonResponse({'success': True, 'students': results})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)

    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)


# Add to groups/views.py

from django.contrib.auth.decorators import login_required, user_passes_test


def is_student(user):
    return user.is_authenticated and hasattr(user, 'student_profile')


@login_required
@user_passes_test(is_student, login_url='/login/')
def student_groups(request):
    """Student group dashboard - only accessible by students"""
    try:
        student = request.user.student_profile

        # Get student's groups through GroupMembership
        memberships = GroupMembership.objects.filter(student=student).select_related('group')

        # Get groups with additional data
        groups_data = []
        for membership in memberships:
            group = membership.group

            # Get attendance rate for this student in this group
            attendance_records = Attendance.objects.filter(
                student=student,
                group=group
            )

            if attendance_records.exists():
                present_count = attendance_records.filter(status='present').count()
                attendance_rate = round((present_count / attendance_records.count()) * 100)
            else:
                attendance_rate = 0

            # Get upcoming exams for this group
            upcoming_exams = Exam.objects.filter(
                group=group,
                date__gte=timezone.now()
            ).order_by('date')[:2]

            # Get pending homework for this group
            pending_homework = Homework.objects.filter(
                assigned_to=group,
                due_date__gte=timezone.now()
            ).order_by('due_date')[:5]

            groups_data.append({
                'group': group,
                'membership': membership,
                'attendance_rate': attendance_rate,
                'upcoming_exams': upcoming_exams,
                'pending_homework': pending_homework,
                'homework_count': pending_homework.count()
            })

        # Calculate overall statistics
        total_groups = len(groups_data)
        total_pending_homework = sum([data['homework_count'] for data in groups_data])

        # Get all upcoming exams
        all_upcoming_exams = Exam.objects.filter(
            group__in=[data['group'] for data in groups_data],
            date__gte=timezone.now()
        ).order_by('date')[:2]

        # Calculate overall attendance rate
        all_attendance = Attendance.objects.filter(student=student)
        overall_attendance_rate = 0
        if all_attendance.exists():
            present_count = all_attendance.filter(status='present').count()
            overall_attendance_rate = round((present_count / all_attendance.count()) * 100)

        any_homework = any([data['homework_count'] > 0 for data in groups_data])
        any_exams = any([data['upcoming_exams'].exists() for data in groups_data])

        context = {
            'student': student,
            'groups_data': groups_data,
            'total_groups': total_groups,
            'total_pending_homework': total_pending_homework,
            'upcoming_exams_count': all_upcoming_exams.count(),
            'overall_attendance_rate': overall_attendance_rate,
            'user': request.user,
            'now': timezone.now(),
            'any_homework': any_homework,
            'any_exams': any_exams,
        }

        return render(request, 'student/student_group.html', context)

    except Exception as e:
        messages.error(request, f"Error loading dashboard: {str(e)}")
        return render(request, 'student/student_group.html', {})


@login_required
@user_passes_test(is_student, login_url='/login/')
def student_attendance(request):
    """Student attendance dashboard - only accessible by students"""
    try:
        student = request.user.student_profile

        # Get filter parameters
        subject_filter = request.GET.get('subject', 'all')
        time_filter = request.GET.get('time_filter', 'all')
        status_filter = request.GET.get('status', 'all')
        search_query = request.GET.get('search', '')

        # Get student's attendance records
        attendance_records = Attendance.objects.filter(
            student=student
        ).select_related('group', 'group__subject', 'recorded_by').order_by('-date')

        # Apply filters
        if subject_filter != 'all':
            attendance_records = attendance_records.filter(group__subject__name=subject_filter)

        if status_filter != 'all':
            attendance_records = attendance_records.filter(status=status_filter)

        if time_filter != 'all':
            today = timezone.now().date()
            if time_filter == 'week':
                week_ago = today - timedelta(days=7)
                attendance_records = attendance_records.filter(date__gte=week_ago)
            elif time_filter == 'month':
                month_ago = today - timedelta(days=30)
                attendance_records = attendance_records.filter(date__gte=month_ago)
            elif time_filter == '3months':
                three_months_ago = today - timedelta(days=90)
                attendance_records = attendance_records.filter(date__gte=three_months_ago)

        # Apply search
        if search_query:
            attendance_records = attendance_records.filter(
                Q(group__name__icontains=search_query) |
                Q(group__subject__name__icontains=search_query) |
                Q(recorded_by__first_name__icontains=search_query) |
                Q(recorded_by__last_name__icontains=search_query)
            )

        # Calculate statistics
        total_attendance = Attendance.objects.filter(student=student)
        present_count = total_attendance.filter(status='present').count()
        absent_count = total_attendance.filter(status='absent').count()
        late_count = total_attendance.filter(status='late').count()
        excused_count = total_attendance.filter(status='excused').count()

        total_records = total_attendance.count()
        overall_attendance_rate = round((present_count / total_records * 100)) if total_records > 0 else 0

        # Get unique subjects for filter dropdown
        subjects = Subject.objects.filter(
            group__groupmembership__student=student
        ).distinct()

        context = {
            'student': student,
            'attendance_records': attendance_records,
            'subjects': subjects,
            'overall_attendance_rate': overall_attendance_rate,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'excused_count': excused_count,
            'total_records': total_records,
            'selected_subject': subject_filter,
            'selected_time_filter': time_filter,
            'selected_status': status_filter,
            'search_query': search_query,
            'user': request.user,
        }

        return render(request, 'student/student_attendance.html', context)

    except Exception as e:
        messages.error(request, f"Error loading attendance: {str(e)}")
        return render(request, 'student/student_attendance.html', {})