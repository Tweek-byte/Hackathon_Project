from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.quiz_dashboard, name='quiz_dashboard'),
    path('create/', views.create_quiz, name='create_quiz'),
    path('upload-material/', views.upload_material, name='upload_material'),
    path('edit-quiz/<int:quiz_id>/', views.edit_quiz, name='edit_quiz'),
    path('publish-quiz/<int:quiz_id>/', views.publish_quiz, name='publish_quiz'),
    path('delete/<int:quiz_id>/', views.delete_quiz, name='delete_quiz'),
    # Course Materials URLs
    path('course-materials/', views.course_materials_list, name='course_materials'),
    path('course-materials/upload/', views.upload_course_material, name='upload_course_material'),
    path('course-materials/delete/<int:material_id>/', views.delete_course_material, name='delete_material'),
] 