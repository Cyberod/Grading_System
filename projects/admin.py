from django.contrib import admin
from .models import Project, Grade

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'teacher', 'is_submitted', 'submitted_at', 'due_date')
    list_filter = ('is_submitted', 'teacher', 'submitted_at')
    search_fields = ('title', 'student__username', 'teacher__username')
    date_hierarchy = 'submitted_at'

@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('project', 'teacher', 'score', 'letter_grade', 'graded_at')
    list_filter = ('letter_grade', 'teacher', 'graded_at')
    search_fields = ('project__title', 'project__student__username')
    readonly_fields = ('letter_grade', 'graded_at')
