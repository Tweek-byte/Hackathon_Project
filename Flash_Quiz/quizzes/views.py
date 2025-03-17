from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Material, Quiz, Question, Choice, StudentQuiz, CourseMaterial
from accounts.models import Enrollment
import PyPDF2
import requests
from django.conf import settings
import os
import json
from huggingface_hub import InferenceClient
from .forms import QuizForm

# Initialize only Hugging Face client
client = InferenceClient(token=settings.HUGGINGFACE_API_KEY)

# Create your views here.

@login_required
def quiz_dashboard(request):
    if not request.user.is_professor():
        return redirect('home')
        
    quizzes = Quiz.objects.filter(professor=request.user).order_by('-created_at')
    context = {
        'quizzes': quizzes,
    }
    return render(request, 'quizzes/dashboard.html', context)

@login_required
def edit_quiz(request, quiz_id):
    if not request.user.is_professor():
        return redirect('home')
        
    quiz = get_object_or_404(Quiz, id=quiz_id, professor=request.user)
    
    if request.method == 'POST':
        form = QuizForm(request.POST, instance=quiz)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.department = request.user.department
            quiz.save()
            
            # Handle questions if they were updated
            questions_data = json.loads(request.POST.get('questions', '[]'))
            if questions_data:
                # Delete existing questions
                quiz.questions.all().delete()
                
                # Create new questions
                for q_data in questions_data:
                    question = Question.objects.create(
                        quiz=quiz,
                        text=q_data['text'],
                        type='multiple_choice'
                    )
                    
                    for i, choice_text in enumerate(q_data['choices']):
                        Choice.objects.create(
                            question=question,
                            text=choice_text,
                            is_correct=(i == q_data['correct_index'])
                        )
            
            messages.success(request, 'Quiz updated successfully!')
            return redirect('quiz_dashboard')
    else:
        form = QuizForm(instance=quiz)
        
    context = {
        'form': form,
        'quiz': quiz,
        'questions': quiz.questions.all().prefetch_related('choices')
    }
    return render(request, 'quizzes/edit_quiz.html', context)

@login_required
def upload_material(request):
    if not request.user.is_professor():
        return redirect('home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        pdf_file = request.FILES.get('material')
        
        if pdf_file and title:
            # Create material
            material = Material.objects.create(
                title=title,
                file=pdf_file,
                professor=request.user
            )
            
            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            
            material.content_text = text_content
            material.save()
            
            messages.success(request, 'Material uploaded successfully!')
            return redirect('generate_quiz', material_id=material.id)
        else:
            messages.error(request, 'Please provide both title and PDF file.')
            
    return render(request, 'quizzes/upload_material.html')

@login_required
def generate_quiz(request, material_id):
    if not request.user.is_professor():
        return redirect('home')
        
    material = get_object_or_404(Material, id=material_id, professor=request.user)
    
    try:
        # Extract text from PDF
        pdf_reader = PyPDF2.PdfReader(material.file.path)
        text_content = ""
        for page in pdf_reader.pages:
            text_content += page.extract_text()

        # Call Deepseek API to generate questions
        api_key = settings.DEEPSEEK_API_KEY
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        prompt = f"""Based on the following material, generate 10 multiple choice questions. 
        Format each question as JSON with the following structure:
        {{
            "question": "question text",
            "choices": ["choice1", "choice2", "choice3", "choice4"],
            "correct_answer": 0  // index of correct choice
        }}
        Material content: {text_content[:4000]}  // Limiting content length for API
        """
        
        response = requests.post(
            'https://api.deepseek.com/v1/chat/completions',  # Replace with actual Deepseek endpoint
            headers=headers,
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        
        if response.status_code == 200:
            questions_data = response.json()['choices'][0]['message']['content']
            # Parse the response and create quiz with questions
            quiz = Quiz.objects.create(
                title=f"Quiz for {material.title}",
                material=material,
                professor=request.user,
                department=request.user.department,
                status='draft'
            )
            
            # Create questions and choices
            for q_data in questions_data:
                question = Question.objects.create(
                    quiz=quiz,
                    text=q_data['question']
                )
                
                for i, choice_text in enumerate(q_data['choices']):
                    Choice.objects.create(
                        question=question,
                        text=choice_text,
                        is_correct=(i == q_data['correct_answer'])
                    )
            
            messages.success(request, 'Quiz generated successfully!')
            return redirect('edit_quiz', quiz_id=quiz.id)
            
        else:
            messages.error(request, 'Error generating questions. Please try again.')
            
    except Exception as e:
        messages.error(request, f'Error generating quiz: {str(e)}')
    
    return redirect('quiz_dashboard')

@login_required
def publish_quiz(request, quiz_id):
    if not request.user.is_professor():
        return redirect('home')
        
    quiz = get_object_or_404(Quiz, id=quiz_id, professor=request.user)
    
    if quiz.status == 'draft':
        quiz.status = 'published'
        quiz.save()
        messages.success(request, 'Quiz published successfully!')
    else:
        messages.error(request, 'Quiz is already published!')
        
    return redirect('quiz_dashboard')

@login_required
def available_quizzes(request):
    if not request.user.is_student():
        return redirect('home')
        
    # Get student's verified enrollments
    verified_enrollments = Enrollment.objects.filter(
        student=request.user,
        is_verified=True
    ).values_list('professor_id', flat=True)
    
    # Get available quizzes
    current_time = timezone.now()
    available_quizzes = Quiz.objects.filter(
        professor_id__in=verified_enrollments,
        department=request.user.major,
        semester=request.user.semester,
        status='published',
        start_time__lte=current_time,
        end_time__gte=current_time
    ).exclude(
        studentquiz__student=request.user  # Exclude already taken quizzes
    )
    
    context = {
        'quizzes': available_quizzes
    }
    return render(request, 'quizzes/available_quizzes.html', context)

@login_required
def course_materials_list(request):
    if request.user.is_professor():
        materials = CourseMaterial.objects.filter(professor=request.user).order_by('-uploaded_at')
    else:
        materials = CourseMaterial.objects.filter(
            department=request.user.major,
            semester=request.user.semester
        ).order_by('-uploaded_at')
    return render(request, 'materials/materials_list.html', {'materials': materials})

@login_required
def upload_course_material(request):
    if not request.user.is_professor():
        return redirect('home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        pdf_file = request.FILES.get('material')
        department = request.POST.get('department')
        semester = request.POST.get('semester')
        
        if pdf_file and title:
            try:
                material = CourseMaterial.objects.create(
                    title=title,
                    description=description,
                    file=pdf_file,
                    professor=request.user,
                    department=department,
                    semester=semester
                )
                messages.success(request, 'Course material uploaded successfully!')
                return redirect('materials_list')
            except Exception as e:
                messages.error(request, f'Error uploading material: {str(e)}')
        else:
            messages.error(request, 'Please provide all required fields.')
    
    return render(request, 'materials/upload_material.html')

@login_required
def delete_course_material(request, material_id):
    if not request.user.is_professor():
        return redirect('home')
        
    material = get_object_or_404(CourseMaterial, id=material_id, professor=request.user)
    
    if request.method == 'POST':
        try:
            # Delete the file from storage
            if material.file:
                if os.path.isfile(material.file.path):
                    os.remove(material.file.path)
            # Delete the database record
            material.delete()
            messages.success(request, 'Course material deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting material: {str(e)}')
    
    return redirect('materials_list')

@login_required
def create_quiz(request):
    if not request.user.is_professor():
        return redirect('home')
        
    if request.method == 'POST':
        title = request.POST.get('title')
        semester = request.POST.get('semester')
        duration = request.POST.get('duration_minutes')
        pdf_file = request.FILES.get('material')
        
        if not all([title, semester, duration, pdf_file]):
            messages.error(request, 'Please fill all required fields')
            return redirect('create_quiz')
            
        try:
            # Create material first
            material = Material.objects.create(
                title=title,
                file=pdf_file,
                professor=request.user
            )

            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            
            material.content_text = text_content
            material.save()

            # Create quiz
            quiz = Quiz.objects.create(
                title=title,
                professor=request.user,
                material=material,
                department=request.user.department,
                semester=semester,
                duration_minutes=duration,
                status='draft'
            )

            print("Starting question generation with Hugging Face...")
            
            try:
                # Prepare the prompt
                prompt = f"""Generate 10 multiple choice questions based on this educational content.
                Format your response as a JSON array. Each question should have:
                - "text": the question text
                - "choices": array of 4 possible answers
                - "correct_index": number 0-3 indicating the correct answer

                Content: {text_content[:3000]}

                Respond with only a JSON array like this:
                [
                    {{
                        "text": "What is...?",
                        "choices": ["A", "B", "C", "D"],
                        "correct_index": 0
                    }},
                    ...
                ]"""

                # Call Hugging Face API
                response = client.text_generation(
                    prompt,
                    model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                    max_new_tokens=2000,
                    temperature=0.7,
                    repetition_penalty=1.2
                )

                print(f"Raw API Response: {response}")

                # Find JSON in response
                response_text = response
                json_start = response_text.find('[')
                json_end = response_text.rfind(']') + 1

                if json_start == -1 or json_end == -1:
                    raise ValueError("No JSON found in response")

                json_str = response_text[json_start:json_end]
                print(f"Extracted JSON: {json_str}")

                questions_data = json.loads(json_str)

                # Create questions and choices
                for q_data in questions_data:
                    question = Question.objects.create(
                        quiz=quiz,
                        text=q_data['text'],
                        type='multiple_choice'
                    )
                    
                    for i, choice_text in enumerate(q_data['choices']):
                        Choice.objects.create(
                            question=question,
                            text=choice_text,
                            is_correct=(i == q_data['correct_index'])
                        )
                
                messages.success(request, 'Quiz created successfully with AI-generated questions!')
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error: {str(e)}")
                print(f"Attempted to parse: {json_str}")
                messages.warning(request, 'Quiz created but error parsing AI response')
            except Exception as e:
                print(f"Error during question generation: {str(e)}")
                print(f"Error type: {type(e)}")
                messages.warning(request, f'Quiz created but error generating questions: {str(e)}')
            
            return redirect('edit_quiz', quiz_id=quiz.id)
            
        except Exception as e:
            messages.error(request, f'Error creating quiz: {str(e)}')
            return redirect('create_quiz')
            
    return render(request, 'pages/create_quiz.html')

@login_required
def delete_quiz(request, quiz_id):
    if not request.user.is_professor():
        return redirect('home')
        
    quiz = get_object_or_404(Quiz, id=quiz_id, professor=request.user)
    
    if request.method == 'POST':
        try:
            # Delete associated material if it exists
            if quiz.material:
                if quiz.material.file:
                    if os.path.isfile(quiz.material.file.path):
                        os.remove(quiz.material.file.path)
                quiz.material.delete()
            
            # Delete the quiz
            quiz.delete()
            messages.success(request, 'Quiz deleted successfully!')
        except Exception as e:
            messages.error(request, f'Error deleting quiz: {str(e)}')
    
    return redirect('quiz_dashboard')
