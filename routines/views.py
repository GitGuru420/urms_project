from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Faculty, Department, Teacher, Room, Course, TimeSlot, Routine, User

# ==============================================================================
# PUBLIC FACING INTERFACES
# ==============================================================================
def landing_page(request):
    """Simple clean landing page with 'View Routine' and 'Login' target actions"""
    return render(request, 'routines/landing.html')


def view_routine(request):
    """Public filter engine to lookup schedules by Day, Department, Semester, and Group"""
    days = [choice[0] for choice in Routine.DAYS_OF_WEEK]
    departments = Department.objects.all()
    
    # Fetch filter states from the user search submission
    selected_day = request.GET.get('day')
    selected_dept = request.GET.get('department')
    selected_semester = request.GET.get('semester')
    selected_group = request.GET.get('group_no')
    
    routines = None
    search_triggered = False

    if selected_day and selected_dept and selected_semester and selected_group:
        search_triggered = True
        # Extract the complete timeline layout blocks matching criteria
        routines = Routine.objects.filter(
            day_of_week=selected_day,
            department_id=selected_dept,
            semester=selected_semester,
            group_no=selected_group
        ).order_with_respect_to('start_time') # Keep it arranged from morning to afternoon

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
    """Processes user access control and routes them to their specific dashboard tier"""
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
            messages.error(request, "Invalid identification ID credentials or password.")
            
    return render(request, 'routines/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Logged out successfully.")
    return redirect('landing_page')


def route_user_dashboard(user):
    """Helper method to steer logged-in users to their authorized spaces"""
    if user.role == User.Role.FACULTY_ADMIN or user.is_superuser:
        return redirect('faculty_admin_dashboard')
    elif user.role == User.Role.DEPT_ADMIN:
        return redirect('dept_admin_dashboard')
    elif user.role == User.Role.TEACHER:
        return redirect('teacher_dashboard')
    return redirect('landing_page')


# ==============================================================================
# ROLE-BASED DASHBOARD PLATFORMS
# ==============================================================================
@login_required
def faculty_admin_dashboard(request):
    """Tier 1 Space: Handles multi-department reports, exports, and profile creations"""
    if not (request.user.role == User.Role.FACULTY_ADMIN or request.user.is_superuser):
        return redirect('landing_page')
    return render(request, 'routines/faculty_admin.html')


@login_required
def dept_admin_dashboard(request):
    """Tier 2 Space: Controls classroom inventories, courses, and schedules entries"""
    if not request.user.role == User.Role.DEPT_ADMIN:
        return redirect('landing_page')
    return render(request, 'routines/dept_admin.html')


@login_required
def teacher_dashboard(request):
    """Tier 3 Space: Provides personal schedule matrix summaries for teachers"""
    if not request.user.role == User.Role.TEACHER:
        return redirect('landing_page')
    return render(request, 'routines/teacher_dashboard.html')