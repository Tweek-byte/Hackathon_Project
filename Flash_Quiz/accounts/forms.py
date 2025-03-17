from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from .models import User

User = get_user_model()

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'profile_picture']
        if User.role == 'student':
            fields.extend(['major', 'semester'])
        elif User.role == 'professor':
            fields.append('department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # Make fields optional to allow partial updates
        self.fields['username'].required = False
        self.fields['email'].required = False
        self.fields['first_name'].required = False
        self.fields['last_name'].required = False
        self.fields['profile_picture'].required = False

class UserRegistrationForm(UserCreationForm):
    SEMESTER_CHOICES = [
        (1, '1st Semester'),
        (2, '2nd Semester'),
        (3, '3rd Semester'),
        (4, '4th Semester'),
        (5, '5th Semester'),
        (6, '6th Semester'),
        (7, '7th Semester'),
        (8, '8th Semester')
    ]

    MAJOR_CHOICES = [
        ('Computer Science', 'Computer Science'),
        ('Mathematics', 'Mathematics'),
        ('Physics', 'Physics'),
        ('Chemistry', 'Chemistry'),
        ('Biology', 'Biology'),
        ('Engineering', 'Engineering'),
        ('English', 'English')
    ]

    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=User.ROLE_CHOICES)
    department = forms.ChoiceField(
        choices=User.DEPARTMENT_CHOICES,
        required=False
    )
    major = forms.CharField(required=False)
    semester = forms.IntegerField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'role', 'department', 'major', 'semester']

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        department = cleaned_data.get('department')
        major = cleaned_data.get('major')
        semester = cleaned_data.get('semester')

        if role == 'professor' and not department:
            self.add_error('department', 'Department is required for professors')
        elif role == 'student':
            if not major:
                self.add_error('major', 'Major is required for students')
            if not semester:
                self.add_error('semester', 'Semester is required for students')
        elif role == 'professor':
            cleaned_data['semester'] = None

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'}) 