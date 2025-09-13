from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()

class Project(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_projects')
    file_upload = models.FileField(upload_to='projects/', null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateTimeField()
    is_submitted = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.student.username}"

class Grade(models.Model):
    GRADE_CHOICES = [
        ('A+', 'A+ (90-100)'),
        ('A', 'A (80-89)'),
        ('B+', 'B+ (70-79)'),
        ('B', 'B (60-69)'),
        ('C+', 'C+ (50-59)'),
        ('C', 'C (40-49)'),
        ('D', 'D (30-39)'),
        ('F', 'F (0-29)'),
    ]
    
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='grade')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grades_given')
    score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score out of 100"
    )
    letter_grade = models.CharField(max_length=2, choices=GRADE_CHOICES, blank=True)
    feedback = models.TextField(blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Auto-assign letter grade based on score
        if self.score >= 90:
            self.letter_grade = 'A+'
        elif self.score >= 80:
            self.letter_grade = 'A'
        elif self.score >= 70:
            self.letter_grade = 'B+'
        elif self.score >= 60:
            self.letter_grade = 'B'
        elif self.score >= 50:
            self.letter_grade = 'C+'
        elif self.score >= 40:
            self.letter_grade = 'C'
        elif self.score >= 30:
            self.letter_grade = 'D'
        else:
            self.letter_grade = 'F'
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.project.title} - {self.letter_grade} ({self.score}%)"
