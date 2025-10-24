from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import StudentProfile, Student

@receiver(post_save, sender=StudentProfile)
def link_student_to_profile(sender, instance, created, **kwargs):
    if created:
        try:
            student = Student.objects.get(index_number=instance.index_number)
            instance.student = student
            instance.save()
        except Student.DoesNotExist:
            pass
