from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Faculty, Department, FacultyAdminProfile, 
    DeptAdminProfile, Teacher, Room, Course, TimeSlot, Routine
)

# Customize the main User layout to display our specific 'role' column
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['username', 'email', 'role', 'is_staff', 'is_superuser']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Management', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Management', {'fields': ('role',)}),
    )

# Clean columnar grids for standard master datasets
@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['id', 'name']
    search_fields = ['name']

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'faculty']
    list_filter = ['faculty']
    search_fields = ['name']

@admin.register(FacultyAdminProfile)
class FacultyAdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'faculty']

@admin.register(DeptAdminProfile)
class DeptAdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['teacher_id', 'name', 'department']
    search_fields = ['name', 'teacher_id']
    list_filter = ['department']

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['room_number', 'department', 'is_online']
    list_filter = ['is_online', 'department']
    search_fields = ['room_number']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['course_code', 'title', 'department']
    search_fields = ['course_code', 'title']
    list_filter = ['department']

@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ['name', 'start_time', 'end_time']

@admin.register(Routine)
class RoutineAdmin(admin.ModelAdmin):
    list_display = ['department', 'day_of_week', 'semester', 'group_no', 'section', 'course', 'teacher', 'room']
    list_filter = ['day_of_week', 'department', 'semester']
    search_fields = ['group_no', 'course__course_code', 'teacher__name']

# Register the core user model custom layout
admin.site.register(User, CustomUserAdmin)