from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from quizzes.models import Quiz, QuizResult, StudentQuiz, Material
from django.contrib import messages
from django.urls import reverse_lazy
import PyPDF2

class HomeView(TemplateView):
    template_name = 'pages/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context['is_professor'] = self.request.user.is_professor()
        return context

class QuizListView(LoginRequiredMixin, ListView):
    model = Quiz
    template_name = 'pages/quiz_list.html'
    context_object_name = 'quizzes'

    def get_queryset(self):
        if self.request.user.is_professor():
            return Quiz.objects.filter(professor=self.request.user)
        else:
            # For students, show only published quizzes in their major and semester
            return Quiz.objects.filter(
                status='published',
                department=self.request.user.major,
                semester=self.request.user.semester
            )

class StudentResultsView(LoginRequiredMixin, ListView):
    model = StudentQuiz
    template_name = 'pages/student_results.html'
    context_object_name = 'results'

    def get_queryset(self):
        if self.request.user.is_student():
            return StudentQuiz.objects.filter(student=self.request.user)
        return StudentQuiz.objects.none()

class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'pages/profile.html'

class QuizCreateView(LoginRequiredMixin, CreateView):
    model = Quiz
    template_name = 'pages/create_quiz.html'
    success_url = reverse_lazy('quiz_dashboard')
    fields = ['title', 'semester', 'duration_minutes']

    def form_valid(self, form):
        if not self.request.user.is_professor():
            return self.handle_no_permission()
            
        pdf_file = self.request.FILES.get('material')
        if not pdf_file:
            messages.error(self.request, 'Please upload a PDF file')
            return self.form_invalid(form)

        try:
            # Create material first
            material = Material.objects.create(
                title=form.cleaned_data['title'],
                file=pdf_file,
                professor=self.request.user
            )

            # Extract text from PDF
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text_content = ""
            for page in pdf_reader.pages:
                text_content += page.extract_text()
            
            material.content_text = text_content
            material.save()

            # Set quiz attributes
            form.instance.professor = self.request.user
            form.instance.material = material
            form.instance.department = self.request.user.department
            form.instance.status = 'draft'

            messages.success(self.request, 'Quiz created successfully! Now generating questions...')
            return super().form_valid(form)

        except Exception as e:
            messages.error(self.request, f'Error creating quiz: {str(e)}')
            return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_professor():
            return self.handle_no_permission()
        return super().dispatch(request, *args, **kwargs)

class StudentMarksView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = QuizResult
    template_name = 'pages/student_marks.html'
    context_object_name = 'results'

    def test_func(self):
        return self.request.user.is_professor()

    def get_queryset(self):
        return QuizResult.objects.all().order_by('-completed_at')