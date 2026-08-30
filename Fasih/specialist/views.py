from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from patient.models import Patient
from specialist.models import Specialist, SpecialistCertificate
from accounts.models import User
from assessment.models import Assessment
from accounts.forms import UserProfileForm, SpecialistProfileForm
from specialist.forms import SpecialistCertificateForm
from session.models import Session
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone



@login_required
def specialist_home(request):

    if request.user.role != User.Role.SPECIALIST:
        return redirect("main:home")

    specialist = get_object_or_404(Specialist, user=request.user)

    if specialist.verification_status != Specialist.VerificationStatus.APPROVED:
        return redirect("accounts:specialist_pending")

    new_consultations_count = Assessment.objects.filter(
        specialist=specialist,
        status='PENDING'
    ).count()

    patients_count = Patient.objects.filter(
        assessments__specialist=specialist,
        assessments__status='ACCEPTED'
    ).distinct().count()

    sessions_count = Session.objects.filter(
        specialist=specialist,
        status=Session.Status.CONFIRMED,
        start_time__gte=timezone.now()
    ).count()

 

    context = {
        "new_consultations_count": new_consultations_count,
        "patients_count": patients_count,
        "sessions_count": sessions_count,
    }

    return render(request, "specialist/specialist_home.html", context)


@login_required
def specialist_patients_dashboard(request):

    if request.user.role != User.Role.SPECIALIST:
        return redirect("main:home")

    specialist = get_object_or_404(Specialist, user=request.user)

    if specialist.verification_status != Specialist.VerificationStatus.APPROVED:
        return redirect("accounts:specialist_pending")

    q = request.GET.get("q", "").strip()

    patients = Patient.objects.filter(
        assessments__specialist=specialist,
        assessments__status='ACCEPTED'
    ).distinct()

    if q:
        patients = patients.filter(
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(file_number__icontains=q)
        )

    patients_data = []

    for patient in patients:
        patients_data.append({
            "id": patient.id,
            "name": patient.user.get_full_name(),
            "file_number": patient.file_number,
            "age": patient.age,
        })

    context = {
        "patients": patients_data,
        "query": q,  
    }

    return render(
        request,
        "specialist/specialist_patients_dashboard.html",
        context
    )


@login_required
def specialist_consultations_dashboard(request):
    specialist = get_object_or_404(Specialist, user=request.user)
    assessments = Assessment.objects.filter(
        status="PENDING",
        specialist=specialist
    ).select_related("patient", "patient__user")

    return render(request, "specialist/specialist_consultations_dashboard.html", {
        "assessments": assessments
    })


def choose_specialist(request):
    specialists = Specialist.objects.filter(
        verification_status=Specialist.VerificationStatus.APPROVED
    )

    context = {
        "specialists": specialists
    }

    return render(request, "specialist/choose_specialist.html", context)


@login_required
def specialist_profile(request):
    user = request.user

    if user.role != User.Role.SPECIALIST:
        return redirect('main:home')

    try:
        specialist = Specialist.objects.get(user=user)
    except Specialist.DoesNotExist:
        return redirect('main:home')
    
    certificates = SpecialistCertificate.objects.filter(
        specialist=specialist
    )

    edit_mode = request.GET.get("edit") == "1"

    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, request.FILES, instance=user)
        specialist_form = SpecialistProfileForm(request.POST, instance=specialist)

        if user_form.is_valid() and specialist_form.is_valid():
            user_form.save()
            specialist_form.save()
            messages.success(request, "تم تحديث البيانات بنجاح")
            return redirect('specialist:specialist_profile')
        else:
            messages.error(request, "تأكد من صحة البيانات المدخلة")
            edit_mode = True   
    else:
        user_form = UserProfileForm(instance=user)
        specialist_form = SpecialistProfileForm(instance=specialist)

    context = {
        'user': user,
        'specialist': specialist,
         "certificates": certificates,
        'user_form': user_form,
        'specialist_form': specialist_form,
        'edit_mode': edit_mode,
    }

    return render(request, 'specialist/specialist_profile.html', context)


@login_required
def edit_certificate(request, cert_id):
    cert = get_object_or_404(
        SpecialistCertificate,
        id=cert_id,
        specialist__user=request.user
    )

    if request.method == "POST":
        form = SpecialistCertificateForm(request.POST, request.FILES, instance=cert)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تحديث الشهادة بنجاح")
            return redirect("specialist:specialist_profile")
    else:
        form = SpecialistCertificateForm(instance=cert)

    return render(request, "specialist/edit_certificate.html", {
        "form": form
    })

@login_required
def delete_certificate(request, cert_id):
    cert = get_object_or_404(
        SpecialistCertificate,
        id=cert_id,
        specialist__user=request.user
    )
    cert.delete()
    messages.success(request, "تم حذف الشهادة")
    return redirect("specialist:specialist_profile")


@login_required
def add_certificate(request):
    if request.user.role != User.Role.SPECIALIST:
        return redirect("main:home")

    specialist = get_object_or_404(Specialist, user=request.user)

    if request.method == "POST":
        form = SpecialistCertificateForm(request.POST, request.FILES)

        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.specialist = specialist
            certificate.save()

            messages.success(request, "تمت إضافة الشهادة بنجاح")
            return redirect("specialist:specialist_profile")
        else:
            print(form.errors)
    else:
        form = SpecialistCertificateForm()

    return render(
        request,
        "specialist/add_certificate.html",
        {"form": form}
    )


@login_required
def specialist_sessions(request):
    if not hasattr(request.user, "specialist"):
        return redirect("main:home")

    sessions = Session.objects.filter(
        specialist=request.user.specialist
    ).order_by("-start_time")

    return render(
        request,
        "specialist/specialist_sessions.html",
        {
            "sessions": sessions
        }
    )


def specialist_detail(request, specialist_id):
    specialist = get_object_or_404(
        Specialist,
        id=specialist_id,
        verification_status=Specialist.VerificationStatus.APPROVED
    )

    certificates = SpecialistCertificate.objects.filter(specialist=specialist)

    can_rate = False
    if request.user.is_authenticated and request.user.role == "PATIENT":
        patient = request.user.patient_profile
        can_rate = Assessment.objects.filter(
            patient=patient,
            specialist=specialist,
            status="ACCEPTED"
        ).exists()

    return render(request, "specialist/specialist_detail.html", {
        "specialist": specialist,
        "certificates": certificates,
        "can_rate": can_rate,
    })