from django.contrib import admin
from .models import Quiz, Question, Choice, Material, StudentQuiz, StudentAnswer

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4

class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'text', 'type']
    list_filter = ['quiz', 'type']
    inlines = [ChoiceInline]
    search_fields = ['text']

class ChoiceAdmin(admin.ModelAdmin):
    list_display = ['question', 'text', 'is_correct']
    list_filter = ['question', 'is_correct']
    search_fields = ['text']

class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'professor', 'created_at']
    list_filter = ['professor', 'created_at']
    search_fields = ['title', 'content_text']

class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'professor', 'department', 'semester', 'status']
    list_filter = ['status', 'department', 'semester', 'professor']
    search_fields = ['title']
    date_hierarchy = 'created_at'

@admin.register(StudentQuiz)
class StudentQuizAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'score', 'completed_at']
    list_filter = ['completed_at']
    search_fields = ['student__username', 'quiz__title']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['student_quiz', 'question', 'is_correct', 'points_earned']
    list_filter = ['is_correct']
    search_fields = ['student_quiz__student__username']

admin.site.register(Quiz, QuizAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Choice, ChoiceAdmin)
admin.site.register(Material, MaterialAdmin)
