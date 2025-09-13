from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.db import models
from .forms import UserRegistrationForm, ProfileUpdateForm, StudentProfileUpdateForm, TeacherProfileUpdateForm
from .models import StudentProfile, TeacherProfile

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f"You are now logged in as {username}.")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})

class UserRegistrationView(CreateView):
    form_class = UserRegistrationForm
    template_name = 'accounts/register.html'
    success_url = reverse_lazy('login')
    
    def form_valid(self, form):
        messages.success(self.request, 'Registration successful! You can now log in.')
        return super().form_valid(form)

@login_required
def dashboard(request):
    user = request.user
    context = {'user': user}
    
    if user.user_type == 'student':
        from projects.models import Project, Grade
        
        # Get student's projects and statistics
        projects = Project.objects.filter(student=user).order_by('-submitted_at')
        graded_projects = projects.filter(grade__isnull=False)
        pending_projects = projects.filter(grade__isnull=True)
        
        # Calculate average grade
        grades = Grade.objects.filter(project__student=user)
        avg_score = grades.aggregate(avg=models.Avg('score'))['avg']
        avg_score = round(avg_score, 1) if avg_score else None
        
        context.update({
            'projects': projects[:5],  # Recent 5 projects
            'total_projects': projects.count(),
            'graded_projects': graded_projects.count(),
            'pending_projects': pending_projects.count(),
            'average_score': avg_score,
        })
        return render(request, 'accounts/student_dashboard.html', context)
        
    elif user.user_type == 'teacher':
        from projects.models import Project, Grade
        
        # Get teacher's assigned projects and statistics
        assigned_projects = Project.objects.filter(teacher=user).order_by('-submitted_at')
        pending_reviews = assigned_projects.filter(grade__isnull=True, is_submitted=True)
        graded_projects = assigned_projects.filter(grade__isnull=False)
        total_students = assigned_projects.values('student').distinct().count()
        
        context.update({
            'recent_submissions': assigned_projects.filter(is_submitted=True)[:5],
            'total_students': total_students,
            'pending_reviews': pending_reviews.count(),
            'graded_projects': graded_projects.count(),
            'total_projects': assigned_projects.count(),
        })
        return render(request, 'accounts/teacher_dashboard.html', context)
    else:
        return render(request, 'accounts/dashboard.html', context)

@login_required
def profile_update(request):
    user = request.user
    
    if request.method == 'POST':
        user_form = ProfileUpdateForm(request.POST, instance=user)
        
        if user.user_type == 'student':
            profile_form = StudentProfileUpdateForm(request.POST, instance=user.student_profile)
        elif user.user_type == 'teacher':
            profile_form = TeacherProfileUpdateForm(request.POST, instance=user.teacher_profile)
        else:
            profile_form = None
        
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user_form.save()
            if profile_form:
                profile_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile_update')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = ProfileUpdateForm(instance=user)
        
        if user.user_type == 'student':
            profile_form = StudentProfileUpdateForm(instance=user.student_profile)
        elif user.user_type == 'teacher':
            profile_form = TeacherProfileUpdateForm(instance=user.teacher_profile)
        else:
            profile_form = None
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/profile_update.html', context)
