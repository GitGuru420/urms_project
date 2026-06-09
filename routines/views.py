from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Faculty, Department, Teacher, Room, Course, TimeSlot, Routine, User, FacultyAdminProfile, DeptAdminProfile

# ==============================================================================
# PUBLIC FACING INTERFACES
# ==============================================================================
def landing_page(request):
    return render(request, 'routines/landing.html')


def view_routine(request):
    days = [choice[0] for choice in Routine.DAYS_OF_WEEK]
    departments = Department.objects.all()
    
    selected_day = request.GET.get('day')
    selected_dept = request.GET.get('department')
    selected_semester = request.GET.get('semester')
    selected_group = request.GET.get('group_no')
    
    routines = None
    search_triggered = False

    if selected_day and selected_dept and selected_semester and selected_group:
        search_triggered = True
        routines = Routine.objects.filter(
            day_of_week=selected_day,
            department_id=selected_dept,
            semester=selected_semester,
            group_no=selected_group
        ).order_by('start_time')

    context = {
        'days': days,
        'departments': departments,
        'routines': routines,
        'search_triggered': search_triggered,
        'queries': request.GET
    }
    return render(request, 'routines/view_routine.html', context)


# ==============================================================================
# SHARED CORE AUTHENTICATION ROUTINES
# ==============================================================================
def login_view(request):
    if request.user.is_authenticated:
        return route_user_dashboard(request.user)

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return route_user_dashboard(user)
        else:
            messages.error(request, "Invalid identification credentials or password.")
            
    return render(request, 'routines/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('landing_page')


def route_user_dashboard(user):
    if user.role == User.Role.FACULTY_ADMIN or user.is_superuser:
        return redirect('faculty_admin_dashboard')
    elif user.role == User.Role.DEPT_ADMIN:
        return redirect('dept_admin_dashboard')
    elif user.role == User.Role.TEACHER:
        return redirect('teacher_dashboard')
    return redirect('landing_page')


# ==============================================================================
# TIER 1: FACULTY ADMIN DASHBOARD ENGINE (Global Admin Controls)
# ==============================================================================
@login_required
def faculty_admin_dashboard(request):
    if not (request.user.role == User.Role.FACULTY_ADMIN or request.user.is_superuser):
        return redirect('landing_page')
        
    departments = Department.objects.all()
    dept_admins = DeptAdminProfile.objects.all()
    all_routines = Routine.objects.all().order_by('day_of_week', 'start_time')

    # Action Handler: Create Department Admin Accounts
    if request.method == 'POST' and 'create_dept_admin' in request.POST:
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        password = request.POST.get('password')
        dept_id = request.POST.get('department')
        
        try:
            if User.objects.filter(username=username).exists():
                raise Exception("Username already exists in the system registry.")
                
            dept = Department.objects.get(id=dept_id)
            new_user = User.objects.create_user(username=username, email=email, password=password, role=User.Role.DEPT_ADMIN)
            DeptAdminProfile.objects.create(user=new_user, department=dept)
            
            messages.success(request, f"Department Admin account '{username}' successfully registered for {dept.name}!")
            return redirect('faculty_admin_dashboard')
        except Exception as e:
            messages.error(request, f"Registration Failed: {str(e)}")

    context = {
        'departments': departments,
        'dept_admins': dept_admins,
        'all_routines': all_routines,
    }
    return render(request, 'routines/faculty_admin.html', context)


# ==============================================================================
# TIER 2: DEPARTMENT ADMIN DASHBOARD ENGINE (Isolated Controls)
# ==============================================================================
@login_required
def dept_admin_dashboard(request):
    if not request.user.role == User.Role.DEPT_ADMIN:
        return redirect('landing_page')
        
    # Isolate active resources to ONLY this administrator's assigned department
    admin_profile = request.user.dept_admin_profile
    my_dept = admin_profile.department
    
    teachers = Teacher.objects.filter(department=my_dept)
    rooms = Room.objects.filter(department=my_dept)
    courses = Course.objects.filter(department=my_dept)
    timeslots = TimeSlot.objects.all()
    my_routines = Routine.objects.filter(department=my_dept).order_by('day_of_week', 'start_time')

    if request.method == 'POST':
        # Action A: Register a new Teacher Account
        if 'create_teacher' in request.POST:
            username = request.POST.get('username')
            password = request.POST.get('password')
            full_name = request.POST.get('full_name')
            teacher_id = request.POST.get('teacher_id')
            
            try:
                if User.objects.filter(username=username).exists() or Teacher.objects.filter(teacher_id=teacher_id).exists():
                    raise Exception("Account with this Username or Teacher ID already exists.")
                    
                new_user = User.objects.create_user(username=username, password=password, role=User.Role.TEACHER)
                Teacher.objects.create(user=new_user, department=my_dept, name=full_name, teacher_id=teacher_id)
                messages.success(request, f"Teacher profile '{full_name}' built successfully.")
                return redirect('dept_admin_dashboard')
            except Exception as e:
                messages.error(request, f"Failed to register teacher: {str(e)}")

        # Action B: Create a Physical/Virtual Classroom Room Unit
        elif 'create_room' in request.POST:
            room_number = request.POST.get('room_number')
            is_online = request.POST.get('is_online') == 'on'
            
            Room.objects.create(department=my_dept, room_number=room_number, is_online=is_online)
            messages.success(request, f"Room environment asset created successfully.")
            return redirect('dept_admin_dashboard')

        # Action C: Create a Routine Schedule Segment entry
        elif 'create_routine' in request.POST:
            course_id = request.POST.get('course')
            teacher_id = request.POST.get('teacher')
            room_id = request.POST.get('room')
            semester = request.POST.get('semester')
            group_no = request.POST.get('group_no')
            section = request.POST.get('section')
            day_of_week = request.POST.get('day_of_week')
            timeslot_id = request.POST.get('timeslot')
            
            try:
                course = Course.objects.get(id=course_id, department=my_dept)
                teacher = Teacher.objects.get(id=teacher_id, department=my_dept)
                room = Room.objects.get(id=room_id, department=my_dept)
                timeslot = TimeSlot.objects.get(id=timeslot_id)
                
                # Instantiating Routine executes the algorithmic cross-department conflicts prevention engine checks
                new_schedule = Routine(
                    department=my_dept, course=course, teacher=teacher, room=room,
                    semester=int(semester), group_no=group_no, section=section,
                    day_of_week=day_of_week, start_time=timeslot.start_time, end_time=timeslot.end_time
                )
                new_schedule.save()
                messages.success(request, "Routine slot successfully scheduled without conflicts!")
                return redirect('dept_admin_dashboard')
            except Exception as e:
                messages.error(request, f"Scheduling Conflict Alert: {str(e)}")

    context = {
        'department': my_dept,
        'teachers': teachers,
        'rooms': rooms,
        'courses': courses,
        'timeslots': timeslots,
        'my_routines': my_routines,
        'days_of_week': [choice[0] for choice in Routine.DAYS_OF_WEEK],
        'sections': Routine.SECTION_CHOICES
    }
    return render(request, 'routines/dept_admin.html', context)


# ==============================================================================
# TIER 3: TEACHER SCHEDULE TRACKER DASHBOARD ENGINE
# ==============================================================================
@login_required
def teacher_dashboard(request):
    if not request.user.role == User.Role.TEACHER:
        return redirect('landing_page')
        
    try:
        teacher_profile = request.user.teacher_profile
    except Teacher.DoesNotExist:
        messages.error(request, "Teacher Profile record metadata was not found.")
        return redirect('landing_page')

    # Fetch all weekly routines where this teacher is assigned across the university
    teacher_routines = Routine.objects.filter(teacher=teacher_profile).order_by('day_of_week', 'start_time')
    days_of_week = [choice[0] for choice in Routine.DAYS_OF_WEEK]

    # Handle summary tracker metric math
    total_weekly_classes = teacher_routines.count()
    
    # Optional Day filter search query parameter block
    selected_day = request.GET.get('day_filter', 'All')
    if selected_day != 'All':
        filtered_routines = teacher_routines.filter(day_of_week=selected_day)
    else:
        filtered_routines = teacher_routines

    context = {
        'teacher': teacher_profile,
        'all_routines': teacher_routines,
        'filtered_routines': filtered_routines,
        'days_of_week': days_of_week,
        'selected_day': selected_day,
        'total_weekly_classes': total_weekly_classes
    }
    return render(request, 'routines/teacher_dashboard.html', context)