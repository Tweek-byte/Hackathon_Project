# AI-Assisted Evaluation System - Flash Quiz

## Overview
This AI-assisted evaluation system enables professors to upload course materials, automatically generate quizzes, and assign them to students based on class (major) and semester. It ensures structured evaluations with anti-cheating measures, real-time notifications, and detailed result tracking.

## Features & Flow

### 1. Authentication & User Roles
#### Signup Flow
- Users select their role during registration:
  - **Professor**: Registers with name, email, password, department/major.
  - **Student**: Registers with name, email, password, major, semester.
- The system assigns them appropriate permissions.

#### Login Flow
- Users log in with their email and password.
- "Forgot Password?" feature allows password resets via email.

### 2. Dashboard
#### Student Dashboard
- **Available Evaluations**: Lists quizzes they can take.
- **Ended Evaluations**: Displays past quizzes.
- **Profile Management**: Edit profile picture, name, email, and password.
- **Evaluation History**: View past quiz results and personal scores.

#### Professor Dashboard
- **Evaluations Overview**: View all created quizzes.
- **Add New Evaluation**: Upload materials and generate quizzes.
- **Student Marks**: View and analyze students’ scores.
- **Profile Management**: Update profile details.

### 3. AI-Generated Quiz Creation
#### Quiz Creation Flow
1. **Upload Course Material**: Accepts PDF, DOCX, or plain text.
2. **AI Processing**: The AI reads the content and generates quiz questions.
3. **Quiz Customization**: The professor can:
   - Edit questions and answers.
   - Change question types (MCQs, True/False, etc.).
   - Set a quiz title.
4. **Assign Quiz**: Select class (major) and semester.
5. **Set Time Limit**: Define quiz start time and duration.
6. **Start Evaluation**: Students can now join and take the quiz.

### 4. Student Quiz-Taking Experience
- Students see an active quiz in "Available Evaluations."
- Upon starting, a **timer begins** counting down.
- They **submit answers** before the time expires.
- A confirmation appears after submission.

### 5. Anti-Cheating Mechanism
- If a student **switches tabs**, the system:
  - Logs the timestamp and duration.
  - Notifies the professor in real-time.
  - (Optional) Warns the student.

### 6. Evaluation Results & Reporting
#### Student View
- Can see only **their own scores** in "Evaluation History."

#### Professor View
- Can view **all students' scores** in "Student Marks."
- Can analyze **quiz performance per student.**

## Tech Stack
### Backend
- **Django (Python)**: Core framework.
- **Django REST Framework**: API development.
- **Celery + Redis**: AI processing & notifications.

### Frontend
- **HTML, CSS, JavaScript**: Core web technologies.
- **React.js or Django Templates**: For UI rendering.

### Database
- **PostgreSQL**: Stores users, quizzes, and results.

### AI Component
- **Deepseek AI**: Analyzes course materials and generates quiz questions.

### Deployment
- **Replit**: Hosting and development.

## Summary
This structured system ensures a seamless experience for both professors and students. The AI component automates quiz generation, while role-based dashboards and anti-cheating mechanisms create a reliable evaluation process.
