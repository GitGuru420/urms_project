from django.urls import path
from . import views

urlpatterns = [
    # Public Views
    path('', views.landing_page, name='landing_page'),
    path('view-routine/', views.view_routine, name='view_routine'),
    
    # Shared Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboards Matrix
    path('dashboard/faculty-admin/', views.faculty_admin_dashboard, name='faculty_admin_dashboard'),
    path('dashboard/dept-admin/', views.dept_admin_dashboard, name='dept_admin_dashboard'),
    path('dashboard/teacher/', views.teacher_dashboard, name='teacher_dashboard'),
]