from django import forms
from django.contrib.auth import get_user_model
from .models import Project, Grade

User = get_user_model()

class ProjectSubmissionForm(forms.ModelForm):
    teacher = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='teacher'),
        empty_label="Select a teacher",
        help_text="Choose the teacher who will grade this project"
    )
    
    class Meta:
        model = Project
        fields = ['title', 'description', 'teacher', 'due_date', 'file_upload']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter project title'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4, 
                'placeholder': 'Describe your project...'
            }),
            'teacher': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'file_upload': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.zip,.rar'
            }),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make teacher field display names nicely
        self.fields['teacher'].queryset = User.objects.filter(user_type='teacher').order_by('first_name', 'last_name')
        self.fields['teacher'].label_from_instance = lambda obj: f"{obj.first_name} {obj.last_name} - {obj.teacher_profile.department if hasattr(obj, 'teacher_profile') else 'N/A'}"
        
        # Add help text
        self.fields['file_upload'].help_text = "Accepted formats: PDF, DOC, DOCX, ZIP, RAR (Max size: 10MB)"
        self.fields['due_date'].help_text = "Select when this project should be submitted by"
        
    def clean_file_upload(self):
        file = self.cleaned_data.get('file_upload')
        if file:
            # Check file size (10MB limit)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB.')
            
            # Check file extension
            allowed_extensions = ['.pdf', '.doc', '.docx', '.zip', '.rar']
            file_extension = '.' + file.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                raise forms.ValidationError(
                    'File type not supported. Please upload PDF, DOC, DOCX, ZIP, or RAR files only.'
                )
        return file
    
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if due_date:
            from django.utils import timezone
            if due_date <= timezone.now():
                raise forms.ValidationError('Due date must be in the future.')
        return due_date
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if title:
            # Remove extra whitespace and ensure minimum length
            title = title.strip()
            if len(title) < 5:
                raise forms.ValidationError('Project title must be at least 5 characters long.')
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description')
        if description:
            description = description.strip()
            if len(description) < 10:
                raise forms.ValidationError('Project description must be at least 10 characters long.')
        return description

class GradeForm(forms.ModelForm):
    RUBRIC_CRITERIA = [
        ('content', 'Content Quality (0-25 points)'),
        ('presentation', 'Presentation/Structure (0-25 points)'),
        ('creativity', 'Creativity/Innovation (0-25 points)'),
        ('technical', 'Technical Implementation (0-25 points)'),
    ]
    
    # Rubric scoring fields
    content_score = forms.IntegerField(
        min_value=0, max_value=25,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        help_text="Quality of content, accuracy, and depth (0-25 points)"
    )
    presentation_score = forms.IntegerField(
        min_value=0, max_value=25,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        help_text="Organization, clarity, and presentation (0-25 points)"
    )
    creativity_score = forms.IntegerField(
        min_value=0, max_value=25,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        help_text="Innovation, originality, and creativity (0-25 points)"
    )
    technical_score = forms.IntegerField(
        min_value=0, max_value=25,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '1'}),
        help_text="Technical execution and implementation (0-25 points)"
    )
    
    class Meta:
        model = Grade
        fields = ['feedback']
        widgets = {
            'feedback': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Provide detailed feedback for the student...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['feedback'].required = False
        
        # If editing existing grade, populate rubric scores
        if self.instance and self.instance.pk and self.instance.score:
            # Distribute existing score evenly across rubric for editing
            avg_score = self.instance.score // 4
            remainder = self.instance.score % 4
            
            self.fields['content_score'].initial = avg_score + (1 if remainder > 0 else 0)
            self.fields['presentation_score'].initial = avg_score + (1 if remainder > 1 else 0)
            self.fields['creativity_score'].initial = avg_score + (1 if remainder > 2 else 0)
            self.fields['technical_score'].initial = avg_score
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Calculate total score from rubric
        content = cleaned_data.get('content_score', 0)
        presentation = cleaned_data.get('presentation_score', 0)
        creativity = cleaned_data.get('creativity_score', 0)
        technical = cleaned_data.get('technical_score', 0)
        
        total_score = content + presentation + creativity + technical
        
        if total_score > 100:
            raise forms.ValidationError('Total score cannot exceed 100 points.')
        
        cleaned_data['calculated_score'] = total_score
        return cleaned_data
    
    def save(self, commit=True):
        grade = super().save(commit=False)
        
        # Calculate total score from rubric
        grade.score = self.cleaned_data['calculated_score']
        
        if commit:
            grade.save()
        return grade

class BulkGradeForm(forms.Form):
    projects = forms.ModelMultipleChoiceField(
        queryset=Project.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )
    score = forms.IntegerField(
        min_value=0, max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text="Score to apply to all selected projects"
    )
    feedback = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Optional feedback for all selected projects...'
        }),
        required=False
    )
    
    def __init__(self, teacher, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show ungraded projects assigned to this teacher
        self.fields['projects'].queryset = Project.objects.filter(
            teacher=teacher,
            grade__isnull=True,
            is_submitted=True
        )
