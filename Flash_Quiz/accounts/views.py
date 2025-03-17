from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_protect
from .serializers import UserRegistrationSerializer, UserSerializer
from django.contrib.auth.decorators import login_required
from .forms import UserProfileForm, UserRegistrationForm
from .models import User, Enrollment

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def register_user(request):
    if request.method == 'POST':
        data = request.POST.copy()  # Make data mutable
        
        # Handle semester field based on role
        if data.get('role') == 'student':
            if data.get('semester'):
                try:
                    data['semester'] = int(data['semester'])
                except ValueError:
                    messages.error(request, 'Semester must be a valid number')
                    return render(request, 'accounts/register.html', {'form': UserRegistrationForm(data)})
            else:
                messages.error(request, 'Semester is required for students')
                return render(request, 'accounts/register.html', {'form': UserRegistrationForm(data)})
        else:  # For professors
            data['semester'] = None  # Set semester to None for professors
            
        form = UserRegistrationForm(data)
        if form.is_valid():
            user = form.save()
            
            # If the user is a student, create enrollment with professors in their department
            if user.role == 'student':
                professors = User.objects.filter(
                    role='professor',
                    department=user.major  # Using major as department for students
                )
                
                for professor in professors:
                    Enrollment.objects.create(
                        student=user,
                        professor=professor,
                        department=user.major,
                        semester=user.semester
                    )
            
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
        else:
            for error in form.errors.values():
                messages.error(request, error[0])
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@csrf_protect
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        try:
            # First get the user by email
            user = User.objects.get(email=email)
            # Then authenticate with username and password
            user = authenticate(request, username=user.username, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, 'Login successful!')
                return redirect('home')
            else:
                messages.error(request, 'Invalid email or password.')
        except User.DoesNotExist:
            messages.error(request, 'Invalid email or password.')
        except Exception as e:
            messages.error(request, 'An error occurred during login.')
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('home')

def password_reset_view(request):
    return render(request, 'accounts/password_reset.html')

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def manage_students(request):
    if not request.user.is_professor():
        return redirect('home')
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        action = request.POST.get('action')
        
        if student_id:
            enrollment = Enrollment.objects.filter(
                professor=request.user,
                student_id=student_id
            ).first()
            
            if enrollment:
                if action == 'verify':
                    enrollment.is_verified = True
                    enrollment.save()
                    messages.success(request, 'Student verified successfully.')
                elif action == 'unverify':
                    enrollment.is_verified = False
                    enrollment.save()
                    messages.success(request, 'Student unverified successfully.')
                elif action == 'remove':
                    enrollment.delete()
                    messages.success(request, 'Student removed from class successfully.')
    
    # Get all enrollments for this professor
    enrollments = Enrollment.objects.filter(
        professor=request.user
    ).select_related('student')

    context = {
        'students': enrollments,
        'semesters': range(1, 9)
    }
    return render(request, 'accounts/manage_students.html', context)

@login_required
def available_classes(request):
    if not request.user.role == 'student':
        return redirect('home')
        
    if request.method == 'POST':
        professor_id = request.POST.get('professor_id')
        action = request.POST.get('action')
        
        try:
            professor = User.objects.get(id=professor_id, role='professor')
            
            if action == 'enroll':
                # Try to enroll
                enrollment, created = Enrollment.objects.get_or_create(
                    student=request.user,
                    professor=professor,
                    department=request.user.major,
                    semester=request.user.semester,
                    defaults={'is_verified': False}
                )
                if created:
                    messages.success(request, f'Successfully enrolled in {professor.department} class.')
                else:
                    messages.info(request, 'You are already enrolled in this class.')
            
            elif action == 'unenroll':
                # Try to unenroll
                deleted = Enrollment.objects.filter(
                    student=request.user,
                    professor=professor
                ).delete()
                if deleted[0] > 0:
                    messages.success(request, f'Successfully unenrolled from {professor.department} class.')
                else:
                    messages.error(request, 'You are not enrolled in this class.')
                    
        except User.DoesNotExist:
            messages.error(request, 'Professor not found.')
            
    # Get all professors in student's major
    available_professors = User.objects.filter(
        role='professor',
        department=request.user.major
    )
    
    # Get current enrollments
    current_enrollments = Enrollment.objects.filter(
        student=request.user
    ).values_list('professor_id', flat=True)
    
    context = {
        'professors': available_professors,
        'current_enrollments': current_enrollments
    }
    return render(request, 'accounts/available_classes.html', context)