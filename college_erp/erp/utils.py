import PyPDF2
import io
import re
from .models import Attendance

def calculate_ats_score(resume_file, job_description=None):
    """Enhanced ATS score calculation based on multiple criteria.

    Args:
        resume_file: file-like object for a PDF resume (readable)
        job_description: optional string containing the job description to compare against
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(resume_file.read()))
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        
        text_lower = text.lower()
        score = 0
        max_score = 100
        
        # 1. Technical Skills (30 points)
        technical_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin', 'go', 'rust', 'typescript'],
            'web': ['html', 'css', 'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'asp.net'],
            'database': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'sqlite', 'dynamodb'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab', 'ci/cd', 'aws', 'azure', 'gcp'],
            'data': ['machine learning', 'deep learning', 'data science', 'pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn']
        }
        
        skills_found = set()
        for category, skills in technical_skills.items():
            for skill in skills:
                if skill in text_lower:
                    skills_found.add(skill)
        
        # Award points based on unique skills found (up to 30 points)
        technical_score = min(len(skills_found) * 2, 30)
        score += technical_score

        # 1.b Job Description match (optional) - bonus up to 20 points
        jd_score = 0
        if job_description:
            jd_text = job_description.lower()
            jd_skills = set()
            for category, skills in technical_skills.items():
                for skill in skills:
                    if ' ' in skill:
                        if skill in jd_text:
                            jd_skills.add(skill)
                    else:
                        if re.search(r"\b" + re.escape(skill) + r"\b", jd_text):
                            jd_skills.add(skill)

            # if JD specified and it has skills, compute overlap
            if jd_skills:
                matched = skills_found.intersection(jd_skills)
                try:
                    ratio = len(matched) / len(jd_skills)
                except Exception:
                    ratio = 0
                jd_score = min(round(ratio * 20), 20)
                score += jd_score
        
        # 2. Contact Information (10 points)
        contact_score = 0
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text):
            contact_score += 5  # Email found
        if re.search(r'\b\d{10}\b|\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b', text):
            contact_score += 5  # Phone number found
        score += contact_score
        
        # 3. Education (15 points)
        education_keywords = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'bca', 'mca', 'b.e', 'm.e', 
                             'degree', 'diploma', 'university', 'college', 'cgpa', 'gpa', 'percentage']
        education_score = 0
        for keyword in education_keywords:
            if keyword in text_lower:
                education_score += 2
                if education_score >= 15:
                    break
        score += min(education_score, 15)
        
        # 4. Experience/Projects (20 points)
        experience_keywords = ['experience', 'worked', 'developed', 'implemented', 'designed', 'built',
                              'project', 'internship', 'achievement', 'accomplishment', 'responsible for']
        experience_count = sum(1 for keyword in experience_keywords if keyword in text_lower)
        experience_score = min(experience_count * 2, 20)
        score += experience_score
        
        # 5. Soft Skills (10 points)
        soft_skills = ['leadership', 'communication', 'teamwork', 'problem solving', 'analytical',
                      'collaboration', 'adaptability', 'time management', 'critical thinking']
        soft_skills_count = sum(1 for skill in soft_skills if skill in text_lower)
        soft_skills_score = min(soft_skills_count * 2, 10)
        score += soft_skills_score
        
        # 6. Certifications (10 points)
        certification_keywords = ['certified', 'certification', 'certificate', 'aws certified',
                                 'google cloud', 'microsoft certified', 'coursera', 'udemy']
        cert_count = sum(1 for keyword in certification_keywords if keyword in text_lower)
        cert_score = min(cert_count * 3, 10)
        score += cert_score
        
        # 7. Formatting and Structure (5 points)
        format_score = 0
        if len(text) > 200:  # Reasonable length
            format_score += 2
        if any(section in text_lower for section in ['experience', 'education', 'skills', 'projects']):
            format_score += 3
        score += format_score
        
        return min(round(score), max_score)
    except Exception as e:
        return 0

def get_attendance_percentage(student, subject=None):
    """Calculate attendance percentage for a student"""
    if subject:
        total = Attendance.objects.filter(student=student, subject=subject).count()
        present = Attendance.objects.filter(student=student, subject=subject, is_present=True).count()
    else:
        total = Attendance.objects.filter(student=student).count()
        present = Attendance.objects.filter(student=student, is_present=True).count()
    
    return round((present / total * 100), 2) if total > 0 else 0


def auto_enroll_student_subjects(student):
    """
    Automatically enrolls a student in all subjects for their department and semester.
    Creates SubjectEnrollment records for subjects matching the student's department and semester.
    
    Args:
        student: Student object to enroll in subjects
    
    Returns:
        tuple: (number of enrollments created, number of enrollments updated)
    """
    from .models import Subject, SubjectEnrollment, Teacher
    
    if not student.department or not student.semester:
        return (0, 0)
    
    # Get all subjects for the student's department and semester
    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.semester
    )
    
    created_count = 0
    updated_count = 0
    
    for subject in subjects:
        # Find a teacher who teaches this subject
        teachers = Teacher.objects.filter(subjects=subject)
        teacher = teachers.first() if teachers.exists() else None
        
        # Create or update enrollment
        enrollment, created = SubjectEnrollment.objects.get_or_create(
            student=student,
            subject=subject,
            defaults={'teacher': teacher}
        )
        
        if created:
            created_count += 1
        else:
            # Update teacher if needed and enrollment already existed
            if teacher and enrollment.teacher != teacher:
                enrollment.teacher = teacher
                enrollment.save()
                updated_count += 1
    
    return (created_count, updated_count)


print("College ERP Models, Forms, and Utils created successfully!")
print("\nNext steps:")
print("1. Install required packages: pip install django psycopg2-binary PyPDF2")
print("2. Create PostgreSQL database: college_erp_db")
print("3. Run migrations: python manage.py makemigrations && python manage.py migrate")
print("4. Create superuser: python manage.py createsuperuser")
print("5. I'll provide the views.py, URLs, and templates in the next artifacts")