from django.urls import path
from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('quiz/create/', views.QuizCreateView.as_view(), name='quiz_create'),
    path('quizzes/', views.QuizListView.as_view(), name='quiz_list'),
    path('results/', views.StudentResultsView.as_view(), name='student_results'),
    path('marks/', views.StudentMarksView.as_view(), name='student_marks'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
]