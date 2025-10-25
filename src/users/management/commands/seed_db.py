# users/management/commands/seed_db.py
import random
from datetime import timedelta, datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import IntegrityError, transaction
from django.contrib.auth import get_user_model

# Try to use Faker if available, otherwise fallback simple generators
try:
    from faker import Faker
    fake = Faker()
except Exception:
    fake = None

User = get_user_model()

# Import your app models
from education.models import Subject, Homework
from groups.models import Group, GroupMembership, Attendance
from exams.models import Exam, Result
from payments.models import Fee
from users.models import Teacher, Student, Parent

def fake_name():
    if fake:
        return fake.name()
    first = random.choice(["Akbar","Dilshod","Anvar","Oybek","Nodir","Zarina","Malika","Nilufar"])
    last = random.choice(["Ibragimov","Karimov","Sultonova","Rahimov","Qodirov","Usmonova"])
    return f"{first} {last}"

def fake_username():
    if fake:
        return fake.user_name()
    return f"user{random.randint(1000,9999)}"

def fake_email():
    if fake:
        return fake.email()
    return f"{fake_username()}@example.com"

class Command(BaseCommand):
    help = "Seed database with fake data for development/testing."

    def add_arguments(self, parser):
        parser.add_argument('--teachers', type=int, default=5, help='Number of teachers to create')
        parser.add_argument('--students', type=int, default=30, help='Number of students to create')
        parser.add_argument('--subjects', type=int, default=6, help='Number of subjects to create')
        parser.add_argument('--groups', type=int, default=6, help='Number of groups to create')

    def handle(self, *args, **options):
        t_count = options['teachers']
        s_count = options['students']
        subj_count = options['subjects']
        group_count = options['groups']

        self.stdout.write(self.style.SUCCESS("Starting DB seed..."))

        with transaction.atomic():
            # 1) Create Subjects
            subjects = []
            for i in range(subj_count):
                name = fake.word() if fake else f"Subject {i+1}"
                code = (fake.lexify(text='??') if fake else f"S{i+1:02d}") + str(random.randint(1,99))
                subj, created = Subject.objects.get_or_create(
                    code=code,
                    defaults={'name': name.title(), 'description': (fake.sentence() if fake else '')}
                )
                subjects.append(subj)
            self.stdout.write(self.style.SUCCESS(f"Created/Found {len(subjects)} subjects"))

            # 2) Create Teachers and teacher profiles
            teachers = []
            for i in range(t_count):
                username = fake_username()
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=fake_email(),
                        password='password123',  # dev password
                        role='teacher',
                        first_name=(fake.first_name() if fake else fake_name().split()[0]),
                        last_name=(fake.last_name() if fake else fake_name().split()[-1]),
                    )
                except IntegrityError:
                    user = User.objects.filter(username=username).first()

                teacher, _ = Teacher.objects.get_or_create(user=user)
                # assign random subjects
                teacher.subjects.set(random.sample(subjects, k=min(len(subjects), random.randint(1,3))))
                teachers.append(teacher)
            self.stdout.write(self.style.SUCCESS(f"Created {len(teachers)} teachers"))

            # 3) Create Students and student profiles
            students = []
            for i in range(s_count):
                username = fake_username()
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=fake_email(),
                        password='password123',
                        role='student',
                        first_name=(fake.first_name() if fake else fake_name().split()[0]),
                        last_name=(fake.last_name() if fake else fake_name().split()[-1]),
                    )
                except IntegrityError:
                    user = User.objects.filter(username=username).first()

                student, _ = Student.objects.get_or_create(user=user)
                students.append(student)
            self.stdout.write(self.style.SUCCESS(f"Created {len(students)} students"))

            # 4) Create Parents and link to random students
            parents = []
            for i in range(max(1, s_count // 6)):
                username = fake_username()
                try:
                    user = User.objects.create_user(
                        username=username,
                        email=fake_email(),
                        password='password123',
                        role='parent',
                        first_name=(fake.first_name() if fake else fake_name().split()[0]),
                        last_name=(fake.last_name() if fake else fake_name().split()[-1]),
                    )
                except IntegrityError:
                    user = User.objects.filter(username=username).first()

                parent, _ = Parent.objects.get_or_create(user=user)
                # link 1-4 students
                linked = random.sample(students, k=min(len(students), random.randint(1,4)))
                parent.students.set(linked)
                parents.append(parent)
            self.stdout.write(self.style.SUCCESS(f"Created {len(parents)} parents"))

            # 5) Create Groups and memberships
            groups = []
            for i in range(group_count):
                name = f"Group {i+1}"
                subj = random.choice(subjects)
                teacher = random.choice(teachers)
                grp, created = Group.objects.get_or_create(
                    name=name,
                    subject=subj,
                    teacher=teacher,
                    defaults={'schedule': {}}
                )
                groups.append(grp)

            # Add students to groups (random)
            for student in students:
                chosen = random.sample(groups, k=random.randint(1, min(2, len(groups))))
                for grp in chosen:
                    GroupMembership.objects.get_or_create(student=student, group=grp)
            self.stdout.write(self.style.SUCCESS(f"Created {len(groups)} groups and memberships"))

            # 6) Create Homeworks
            for i in range(len(groups)*2):
                title = (fake.sentence(nb_words=4) if fake else f"Homework {i+1}")
                grp = random.choice(groups)
                hw, _ = Homework.objects.get_or_create(
                    title=title,
                    subject=grp.subject,
                    assigned_by=grp.teacher,
                    assigned_to=grp,
                    defaults={
                        'due_date': timezone.now() + timedelta(days=random.randint(1,14)),
                        'description': (fake.paragraph() if fake else "Complete exercises."),
                    }
                )
            self.stdout.write(self.style.SUCCESS("Homeworks created"))

            # 7) Create Exams and Results
            exams = []
            for i in range(len(subjects)):
                subj = subjects[i]
                grp = random.choice(groups)
                exam, _ = Exam.objects.get_or_create(
                    name=f"{subj.name} Midterm {random.randint(1,3)}",
                    subject=subj,
                    group=grp,
                    defaults={'date': timezone.now() + timedelta(days=random.randint(1,30)), 'max_score': 100}
                )
                exams.append(exam)

                # Create results for some students in the group
                member_students = list(grp.students.all())
                if not member_students:
                    # try to pick from overall students
                    member_students = students[:5]
                for st in random.sample(member_students, k=min(len(member_students), max(1, len(member_students)//3))):
                    score = random.randint(40, 100)
                    try:
                        Result.objects.create(exam=exam, student=st, score=score, remarks='')
                    except IntegrityError:
                        pass
            self.stdout.write(self.style.SUCCESS("Exams and some results created"))

            # 8) Create Attendance records (random)
            # 8) Create Attendance records (random)
            for grp in groups:
                # take 3 recent dates
                for d in range(3):
                    date = (timezone.now() - timedelta(days=random.randint(0, 10))).date()
                    for st in list(grp.students.all())[:10]:  # limit to 10 per group
                        Attendance.objects.get_or_create(
                            student=st,
                            group=grp,
                            date=date,
                            defaults={
                                'status': random.choice(['present', 'absent', 'late']),
                                'recorded_by': grp.teacher.user  # <-- USER kerak bo'lsa
                                # 'recorded_by': grp.teacher      # <-- TEACHER kerak bo'lsa
                            }
                        )

            self.stdout.write(self.style.SUCCESS("Attendance records created"))

            # 9) Create Fees for students
            for st in students[:min(50, len(students))]:
                for m in range(1):
                    due = (timezone.now() + timedelta(days=random.randint(-30,30))).date()
                    Fee.objects.get_or_create(
                        student=st,
                        amount=random.randint(50,500),
                        due_date=due,
                        defaults={'paid_date': (due if random.choice([True, False]) else None),
                                  'status': random.choice(['paid','pending','overdue'])}
                    )
            self.stdout.write(self.style.SUCCESS("Fees created"))

        self.stdout.write(self.style.SUCCESS("Seeding complete."))
        self.stdout.write(self.style.WARNING("Default passwords for created users are 'password123' — change them in production!"))
