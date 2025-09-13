from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.db.models import Q
from accounts.decorators import student_required, teacher_required
from .models import Project, Grade
from .forms import ProjectSubmissionForm, GradeForm, BulkGradeForm

@login_required
@student_required
def submit_project(request):
    if request.method == 'POST':
        form = ProjectSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            project = form.save(commit=False)
            project.student = request.user
            project.is_submitted = True
            project.save()
            messages.success(request, 'Project submitted successfully!')
            return redirect('my_projects')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProjectSubmissionForm()
    
    return render(request, 'projects/submit_project.html', {'form': form})

@login_required
@student_required
def my_projects(request):
    projects_list = Project.objects.filter(student=request.user).order_by('-submitted_at')
    
    # Pagination
    paginator = Paginator(projects_list, 10)  # Show 10 projects per page
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    return render(request, 'projects/my_projects.html', {'projects': projects})

@login_required
@student_required
def project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, student=request.user)
    
    # Get student statistics
    total_projects = Project.objects.filter(student=request.user).count()
    graded_projects = Project.objects.filter(student=request.user, grade__isnull=False).count()
    
    context = {
        'project': project,
        'total_projects': total_projects,
        'graded_projects': graded_projects,
    }
    return render(request, 'projects/project_detail.html', context)

@login_required
def project_download(request, project_id):
    project = get_object_or_404(Project, id=project_id)
    
    # Students can only download their own projects
    # Teachers can download projects assigned to them
    if request.user.user_type == 'student' and project.student != request.user:
        raise Http404("Project not found.")
    elif request.user.user_type == 'teacher' and project.teacher != request.user:
        raise Http404("Project not found.")
    
    if not project.file_upload:
        messages.error(request, 'No file attached to this project.')
        return redirect('project_detail', project_id=project.id)
    
    from django.http import HttpResponse
    import os
    
    response = HttpResponse(project.file_upload.read(), content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(project.file_upload.name)}"'
    return response

# Teacher Views
@login_required
@teacher_required
def teacher_projects(request):
    # Get search and filter parameters
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset for teacher's assigned projects
    projects_list = Project.objects.filter(teacher=request.user).order_by('-submitted_at')
    
    # Apply search filter
    if search_query:
        projects_list = projects_list.filter(
            Q(title__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__username__icontains=search_query)
        )
    
    # Apply status filter
    if status_filter == 'pending':
        projects_list = projects_list.filter(grade__isnull=True, is_submitted=True)
    elif status_filter == 'graded':
        projects_list = projects_list.filter(grade__isnull=False)
    elif status_filter == 'overdue':
        from django.utils import timezone
        projects_list = projects_list.filter(
            due_date__lt=timezone.now(),
            grade__isnull=True,
            is_submitted=True
        )
    
    # Pagination
    paginator = Paginator(projects_list, 15)  # Show 15 projects per page
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    context = {
        'projects': projects,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    
    return render(request, 'projects/teacher_projects.html', context)

@login_required
@teacher_required
def teacher_project_detail(request, project_id):
    project = get_object_or_404(Project, id=project_id, teacher=request.user)
    
    context = {
        'project': project,
    }
    return render(request, 'projects/teacher_project_detail.html', context)

@login_required
@teacher_required
def grade_project(request, project_id):
    project = get_object_or_404(Project, id=project_id, teacher=request.user)
    
    # Get or create grade instance
    grade, created = Grade.objects.get_or_create(
        project=project,
        defaults={'teacher': request.user, 'score': 0}
    )
    
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=grade)
        if form.is_valid():
            grade = form.save(commit=False)
            grade.teacher = request.user
            grade.project = project
            grade.save()
            
            action = "graded" if created else "updated"
            messages.success(request, f'Project {action} successfully!')
            return redirect('teacher_projects')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = GradeForm(instance=grade)
    
    context = {
        'project': project,
        'form': form,
        'grade': grade,
        'is_editing': not created,
    }
    
    return render(request, 'projects/grade_project.html', context)

@login_required
@teacher_required
def bulk_grade(request):
    if request.method == 'POST':
        form = BulkGradeForm(request.user, request.POST)
        if form.is_valid():
            projects = form.cleaned_data['projects']
            score = form.cleaned_data['score']
            feedback = form.cleaned_data['feedback']
            
            graded_count = 0
            for project in projects:
                grade, created = Grade.objects.get_or_create(
                    project=project,
                    defaults={
                        'teacher': request.user,
                        'score': score,
                        'feedback': feedback
                    }
                )
                if not created:
                    grade.score = score
                    grade.feedback = feedback
                    grade.save()
                
                graded_count += 1
            
            messages.success(request, f'Successfully graded {graded_count} project(s)!')
            return redirect('teacher_projects')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = BulkGradeForm(request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'projects/bulk_grade.html', context)
