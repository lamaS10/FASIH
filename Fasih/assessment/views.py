from email.utils import quote

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from .models import Assessment
from specialist.models import Specialist 
from patient.models import Patient
from django.contrib import messages




def assessment_form(request):
    if not request.user.is_authenticated:
        messages.warning(request,"يرجى تسجيل الدخول أولًا لبدء الاستشارة")

        login_url = reverse('accounts:login')
        current_url = request.get_full_path()

        return redirect(
            f"{login_url}?next={quote(current_url)}&consultation=1"
        )


    specialist_id = request.GET.get("specialist")

    if not specialist_id:
        return redirect("specialist:choose_specialist")

    specialist = get_object_or_404(
        Specialist,
        id=specialist_id,
        verification_status=Specialist.VerificationStatus.APPROVED
    )

    return render(request, "assessment/assessment_form.html", {
        "specialist": specialist
    })



@csrf_exempt
def upload_audio(request):
    if request.method == "POST":
        audio_file = request.FILES.get("audio")
        image_index = request.POST.get("image_index")

        if not audio_file:
            return JsonResponse({"error": "No audio"}, status=400)

        file_name = f"assessment_audio/audio_image_{image_index}.webm"
        saved_path = default_storage.save(file_name, ContentFile(audio_file.read()))

        return JsonResponse({
            "status": "success",
            "file": saved_path
        })

    return JsonResponse({"error": "Invalid method"}, status=405)


@login_required
@csrf_exempt
def submit_assessment(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    data = json.loads(request.body)
    patient = get_object_or_404(
        Patient,
        user=request.user
    )
    specialist_id = data.get("specialist_id")
    specialist = get_object_or_404(
        Specialist,
        id=specialist_id,
        verification_status=Specialist.VerificationStatus.APPROVED
    )
    assessment = Assessment.objects.create(
        patient=patient,
        specialist=specialist,
        assessment_data=data["assessment_data"],
        audio_files=data["assessment_data"].get("images", [])
    )
 
    messages.success(
        request,
        " تم إرسال التقييم إلى الأخصائي بنجاح"
    )

    return JsonResponse({
        "status": "success",
        "assessment_id": assessment.id
    })



@login_required
def assessment_detail(request, id):
    assessment = get_object_or_404(Assessment, id=id)
    specialist = request.user.specialist

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "accept":
            assessment.status = "ACCEPTED"
            assessment.specialist = specialist
            assessment.rejection_reason = None
            assessment.save()
            return redirect("specialist:specialist_patients_dashboard")

     
        elif action == "reject":
            reason = request.POST.get("reason")

            if reason:
                assessment.status = "REJECTED"
                assessment.rejection_reason = reason
                assessment.save()
            return redirect("specialist:specialist_consultations_dashboard")


    dt = assessment.created_at

    if timezone.is_naive(dt):
        dt = dt.replace(tzinfo=timezone.utc)

    dt_riyadh = dt + timedelta(hours=3)

    context = {
        "assessment": assessment,
        "sent_date": dt_riyadh.strftime("%Y / %m / %d"),
        "sent_time": dt_riyadh.strftime("%I:%M %p"),
    }

    return render(request, "assessment/detail.html", context)
