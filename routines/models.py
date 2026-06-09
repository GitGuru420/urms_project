from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError

# CUSTOM CORE USER SYSTEM (Role-Based Access Matrix)
class User(AbstractUser):
    class Role(models.TextChoices):
        SUPERUSER = 'SUPERUSER', 'Superuser'
        FACULTY_ADMIN = 'FACULTY_ADMIN', 'Faculty Admin'
        DEPT_ADMIN = 'DEPT_ADMIN', 'Department Admin'
        TEACHER = 'TEACHER', 'Teacher'

    role = models.CharField(
        max_length=20, 
        choices=Role.choices, 
        default=Role.TEACHER
    )

    def __str__(self):
        return f"{self.username} - {self.get_role_display()}"


# ACADEMIC HIERARCHY INFRASTRUCTURE
class Faculty(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        verbose_name_plural = "Faculties"

    def __str__(self):
        return self.name


class Department(models.Model):
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name

# ROLE PROFILE LAYERS
class FacultyAdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='faculty_admin_profile')
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)

    def __str__(self):
        return f"Faculty Admin: {self.user.username} ({self.faculty.name})"


class DeptAdminProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='dept_admin_profile')
    department = models.ForeignKey(Department, on_delete=models.CASCADE)

    def __str__(self):
        return f"Dept Admin: {self.user.username} ({self.department.name})"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teachers')
    name = models.CharField(max_length=255) 
    teacher_id = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.name} ({self.teacher_id})"


# ASSET RESOURCE ENGINE Models
class Room(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='rooms')
    room_number = models.CharField(max_length=50)
    is_online = models.BooleanField(default=False)

    def __str__(self):
        if self.is_online:
            return f"Online Class Portal ({self.department.name})"
        return f"Room {self.room_number} ({self.department.name})"


class Course(models.Model):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    course_code = models.CharField(max_length=50)
    title = models.CharField(max_length=255)

    def __str__(self):
        return f"[{self.course_code}] {self.title}"


class TimeSlot(models.Model):
    name = models.CharField(max_length=100)  # e.g., Period 1
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.name}: {self.start_time.strftime('%I:%M %p')} - {self.end_time.strftime('%I:%M %p')}"


# ALGORITHMIC CONFLICT CORRELATION ENGINE
class Routine(models.Model):
    DAYS_OF_WEEK = [
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
    ]
    
    SECTION_CHOICES = [
        ('None', 'Theory Session (Full Group - 50 Students)'),
        ('I', 'Lab Sub-Section I (Split Group - 25 Students)'),
        ('II', 'Lab Sub-Section II (Split Group - 25 Students)'),
    ]

    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='routines')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='routines')
    room = models.ForeignKey(Room, on_delete=models.CASCADE)
    
    semester = models.IntegerField()            
    group_no = models.CharField(max_length=10) 
    section = models.CharField(max_length=10, choices=SECTION_CHOICES, default='None') # Handles Lab splits
    
    day_of_week = models.CharField(max_length=15, choices=DAYS_OF_WEEK)
    
    # Decoupled Data Snapshot Strategy Parameters
    start_time = models.TimeField()
    end_time = models.TimeField()

    def clean(self):
        # Find all classes running on the exact same day overlapping this time window
        overlapping_classes = Routine.objects.filter(
            day_of_week=self.day_of_week,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        )

        # Exclude self record if editing an existing scheduled item
        if self.pk:
            overlapping_classes = overlapping_classes.exclude(pk=self.pk)

        # RULE 1: Physical Classroom Double-Booking Check (Ignore if Online)
        if not self.room.is_online:
            room_clash = overlapping_classes.filter(room=self.room).exists()
            if room_clash:
                raise ValidationError(
                    f"Scheduling Conflict: Physical Room '{self.room.room_number}' "
                    f"is already booked by another department/class during this time block."
                )

        # RULE 2: Cross-Departmental Teacher Overlap Check
        teacher_clash = overlapping_classes.filter(teacher=self.teacher).exists()
        if teacher_clash:
            raise ValidationError(
                f"Scheduling Conflict: Teacher '{self.teacher.name}' is already "
                f"assigned to conduct another class session during this time block."
            )

        # RULE 3: Student Batch / Group / Lab Split Conflict Check
        student_clashes = overlapping_classes.filter(
            department=self.department,
            semester=self.semester,
            group_no=self.group_no
        )

        for clash in student_clashes:
            # Conflict occurs if:
            # A) Either class is a whole group Theory session ('None')
            # B) Both classes are specific split Lab sections matching each other (e.g., Section I vs Section I)
            if self.section == 'None' or clash.section == 'None' or self.section == clash.section:
                raise ValidationError(
                    f"Scheduling Conflict: Student Batch [{self.semester}{self.group_no}] "
                    f"(Section Status: {self.get_section_display()}) already has a conflicting assignment."
                )

    def save(self, *args, **kwargs):
        # Enforce validation protocols before writing to database
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.department.name} | Batch {self.semester}{self.group_no} | {self.day_of_week}"