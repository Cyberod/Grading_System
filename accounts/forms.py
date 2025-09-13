from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, StudentProfile, TeacherProfile

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPES, required=True)
    
    # Additional fields based on user type
    student_id = forms.CharField(max_length=20, required=False)
    course = forms.CharField(max_length=100, required=False)
    year_of_study = forms.IntegerField(min_value=1, max_value=6, required=False)
    
    employee_id = forms.CharField(max_length=20, required=False)
    department = forms.CharField(max_length=100, required=False)
    designation = forms.CharField(max_length=50, required=False)
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 
                 'user_type', 'password1', 'password2')
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    
    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        
        if user_type == 'student':
            if not cleaned_data.get('student_id'):
                raise forms.ValidationError("Student ID is required for student accounts.")
            if not cleaned_data.get('course'):
                raise forms.ValidationError("Course is required for student accounts.")
        
        elif user_type == 'teacher':
            if not cleaned_data.get('employee_id'):
                raise forms.ValidationError("Employee ID is required for teacher accounts.")
            if not cleaned_data.get('department'):
                raise forms.ValidationError("Department is required for teacher accounts.")
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone_number = self.cleaned_data['phone_number']
        user.user_type = self.cleaned_data['user_type']
        
        if commit:
            user.save()
            
            # Create profile based on user type
            if user.user_type == 'student':
                StudentProfile.objects.create(
                    user=user,
                    student_id=self.cleaned_data['student_id'],
                    course=self.cleaned_data['course'],
                    year_of_study=self.cleaned_data.get('year_of_study', 1)
                )
            elif user.user_type == 'teacher':
                TeacherProfile.objects.create(
                    user=user,
                    employee_id=self.cleaned_data['employee_id'],
                    department=self.cleaned_data['department'],
                    designation=self.cleaned_data.get('designation', 'Lecturer')
                )
        
        return user

class ProfileUpdateForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['student_id', 'course', 'year_of_study']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Make student_id readonly if it already exists
        if self.instance and self.instance.pk:
            self.fields['student_id'].widget.attrs.update({'readonly': True})

class TeacherProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = TeacherProfile
        fields = ['employee_id', 'department', 'designation']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
        
        # Make employee_id readonly if it already exists
        if self.instance and self.instance.pk:
            self.fields['employee_id'].widget.attrs.update({'readonly': True})
