from django.db import models
from patient.models import Patient
from django.utils import timezone



class Task(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    letter = models.CharField(
        max_length=1,
        help_text="الحرف المستهدف في التمرين"
    )
    duration = models.PositiveIntegerField(
        help_text="مدة التمرين بالدقائق"
    )

    def __str__(self):
        return f"{self.title} - حرف {self.letter}"
    

class PatientTask(models.Model):

    STATUS_CHOICES = [
        ('pending', 'لم تبدأ'),
        ('completed', 'مكتملة'),
        ('late', 'متأخرة'),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='patient_tasks'
    )

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='assigned_tasks'
    )

    due_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    source = models.CharField(
        max_length=30,
        default='manual',
        help_text="manual أو treatment_plan"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.patient} | {self.task} | {self.due_date}"
