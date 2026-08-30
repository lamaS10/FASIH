from django.db import models
from patient.models import Patient
from specialist.models import Specialist
import uuid
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta




class Session(models.Model):

    class Status(models.TextChoices):
        PROPOSED = "PROPOSED", "بانتظار موافقة المريض"
        CONFIRMED = "CONFIRMED", "مؤكدة"
        REJECTED = "REJECTED", "مرفوضة"
        COMPLETED = "COMPLETED", "منتهية"
        CANCELED = "CANCELED", "ملغاة"

    class SessionType(models.TextChoices):
        INITIAL = "INITIAL", "جلسة أولى"
        TREATMENT = "TREATMENT", "جلسة علاجية"

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="sessions")
    specialist = models.ForeignKey(Specialist, on_delete=models.CASCADE, related_name="sessions")

    title = models.CharField(max_length=255)

    room_name = models.CharField(max_length=255, unique=True, editable=False)

    meeting_url = models.URLField(blank=True, null=True)

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROPOSED)
    session_type = models.CharField(max_length=20, choices=SessionType.choices, default=SessionType.TREATMENT)

    patient_response_reason = models.TextField(blank=True, null=True)
    patient_suggested_times = models.TextField(blank=True, null=True)

    # الموعد المقترح الحالي أثناء التفاوض
    proposed_start_time = models.DateTimeField(
        blank=True,
        null=True
    )

    # من صاحب آخر اقتراح
    class ProposedBy(models.TextChoices):
        SPECIALIST = "SPECIALIST", "الأخصائي"
        PATIENT = "PATIENT", "المريض"

    proposed_by = models.CharField(
        max_length=20,
        choices=ProposedBy.choices,
        blank=True,
        null=True
    )

    # عدد المواعيد التي تم اقتراحها
    proposal_count = models.PositiveSmallIntegerField(default=1)

    specialist_joined = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    def can_join(self):
        now = timezone.localtime(timezone.now())
        start = timezone.localtime(self.start_time) - timedelta(minutes=5)
        end = timezone.localtime(self.end_time)

        return (
            self.status == self.Status.CONFIRMED
            and start <= now <= end
        )





    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError("وقت نهاية الجلسة يجب أن يكون بعد وقت البداية")

    def save(self, *args, **kwargs):
        self.full_clean()
        if not self.room_name:
            self.room_name = f"fasih-{uuid.uuid4()}"
        super().save(*args, **kwargs)

class SessionNote(models.Model):
    session = models.OneToOneField(
        Session,
        on_delete=models.CASCADE,
        related_name="note"
    )
    specialist = models.ForeignKey(
        Specialist,
        on_delete=models.CASCADE
    )
    notes = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notes for {self.session}"
