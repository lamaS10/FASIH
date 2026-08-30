from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from datetime import date
from django.utils import timezone
from .models import Patient
from accounts.models import User
from accounts.forms import UserProfileForm, PatientProfileForm
from django.contrib import messages
from session.models import Session
from treatment.models import TreatmentPlan
from assessment.models import Assessment
from django.core.paginator import Paginator
from payment.models import Payment
from treatment.models import calculate_treatment_price
from treatment.models import DailyTask





@login_required
def patient_dashboard(request):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect('main:home')

    try:
        patient = user.patient_profile
    except Patient.DoesNotExist:
        return redirect('accounts:complete_patient_profile')

  

    # مهام اليوم غير المنفذة ضمن الخطة النشطة
    today_tasks_count = DailyTask.objects.filter(
        daily_plan__treatment_plan__patient=patient,
        daily_plan__treatment_plan__status=TreatmentPlan.Status.ACTIVE,
        daily_plan__date=date.today()
    ).exclude(
        status=DailyTask.Status.COMPLETED
    ).count()

    # جميع المهام غير المنفذة ضمن الخطة النشطة
    pending_tasks_count = DailyTask.objects.filter(
        daily_plan__treatment_plan__patient=patient,
        daily_plan__treatment_plan__status=TreatmentPlan.Status.ACTIVE
    ).exclude(
        status=DailyTask.Status.COMPLETED
    ).count()

    has_pending_tasks = pending_tasks_count > 0

    # جلسات بانتظار موافقة المريض
    pending_sessions = patient.sessions.filter(
        status=Session.Status.PROPOSED
    ).order_by("start_time")

    # جلسات مؤكدة حالية أو قادمة
    confirmed_sessions = patient.sessions.filter(
        status=Session.Status.CONFIRMED,
        end_time__gte=timezone.now()
    ).order_by("start_time")

    # هل لدى المريض أي جلسات)
    has_sessions = pending_sessions.exists() or confirmed_sessions.exists()

    # أقرب جلسة مؤكدة 
    next_session = confirmed_sessions.first() if confirmed_sessions.exists() else None
    last_completed_session = patient.sessions.filter(status=Session.Status.COMPLETED).order_by("-start_time").first()
    last_completed_initial_session = patient.sessions.filter(session_type=Session.SessionType.INITIAL,status=Session.Status.COMPLETED).order_by("-start_time").first()


    # الخطة العلاجية
    treatment_plan = TreatmentPlan.objects.filter(
        patient=patient
    ).order_by("-created_at").first()

    if treatment_plan:
        treatment_plan.update_status_if_expired()
    assessment = Assessment.objects.filter(patient=patient).order_by("-created_at").first()
    linked_specialist = None

    has_active_treatment = (treatment_plan
    and treatment_plan.status == TreatmentPlan.Status.ACTIVE)


    first_session = patient.sessions.order_by("created_at").first()
    if first_session:
        linked_specialist = first_session.specialist

    elif assessment and hasattr(assessment, "specialist"):
        linked_specialist = assessment.specialist


    context = {
        'patient': patient,
        'user': user,

        # مهام
        'today_tasks_count': today_tasks_count,
        'pending_tasks_count': pending_tasks_count,
        'has_pending_tasks': has_pending_tasks,

        # جلسات
        'pending_sessions': pending_sessions,
        'confirmed_sessions': confirmed_sessions,
        'has_sessions': has_sessions,
        'next_session': next_session,

        # خطة علاجية
        'treatment_plan': treatment_plan,
        'assessment': assessment,
        "linked_specialist": linked_specialist,
        "last_completed_session": last_completed_session,
        "last_completed_initial_session": last_completed_initial_session,
        "has_active_treatment": has_active_treatment,
        'has_specialist': False,
    }

    return render(request, 'patient/dashboard.html', context)





@login_required
def patient_profile(request):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect('main:home')

    try:
        patient = user.patient_profile
    except Patient.DoesNotExist:
        return redirect('accounts:complete_patient_profile')

    edit_mode = request.GET.get("edit") == "1"


    if request.method == 'POST':
        user_form = UserProfileForm(
            request.POST,
            request.FILES,
            instance=user
        )
        patient_form = PatientProfileForm(
            request.POST,
            instance=patient
        )

        if user_form.is_valid() and patient_form.is_valid():
            user_form.save()
            patient_form.save()
            messages.success(request, "تم تحديث البيانات بنجاح")
            return redirect('patient:profile')

        messages.error(request, "تأكد من صحة البيانات المدخلة")
        edit_mode = True  
    else:
        user_form = UserProfileForm(instance=user)
        patient_form = PatientProfileForm(instance=patient)
    assessment = Assessment.objects.filter(
    patient=patient
    ).order_by("-created_at").first()

    assessment_answers = assessment.assessment_data.get("sections_answers", {}) if assessment else {}
    assessment_images = assessment.assessment_data.get("images", []) if assessment else []
    last_completed_session = Session.objects.filter(patient=patient,session_type=Session.SessionType.INITIAL,status=Session.Status.COMPLETED).order_by("-start_time").first()



    context = {
        'user_form': user_form,
        'patient_form': patient_form,
        'patient': patient,
        'edit_mode': edit_mode, 
        "assessment": assessment,
        "assessment_answers": assessment_answers,
        "assessment_images": assessment_images,
        "last_completed_session": last_completed_session,


    }

    return render(request, 'patient/profile.html', context)

@login_required
def patient_sessions(request):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect('main:home')

    patient = user.patient_profile

    assessment = Assessment.objects.filter(
        patient=patient
    ).order_by("-created_at").first()

    treatment_plan = TreatmentPlan.objects.filter(
        patient=patient
    ).order_by("-created_at").first()
    if treatment_plan:
        treatment_plan.update_status_if_expired()

    #  الجلسة الاستشارية (تشمل PROPOSED و CONFIRMED)
    consultation_sessions = patient.sessions.filter(
        session_type=Session.SessionType.INITIAL
    ).order_by("start_time")

    #  الجلسات العلاجية (غير الاستشارة)
    therapy_sessions = patient.sessions.exclude(
        session_type=Session.SessionType.INITIAL
    ).order_by("start_time")

    can_access_therapy_sessions = (
        treatment_plan is not None
        and treatment_plan.status == TreatmentPlan.Status.ACTIVE
    )

    context = {
        "assessment": assessment,
        "treatment_plan": treatment_plan,
        "consultation_sessions": consultation_sessions,
        "therapy_sessions": therapy_sessions,
        "can_access_therapy_sessions": can_access_therapy_sessions,
    }

    return render(request, "patient/sessions.html", context)

@login_required
def patient_treatment_plan(request):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect("main:home")

    patient = user.patient_profile

    treatment_plans = TreatmentPlan.objects.filter(
        patient=patient
    ).order_by("-created_at")

    for plan in treatment_plans:
        plan.update_status_if_expired()

    assessment = Assessment.objects.filter(
        patient=patient
    ).order_by("-created_at").first()
    last_completed_initial_session = Session.objects.filter(
        patient=patient,
        session_type=Session.SessionType.INITIAL,
        status=Session.Status.COMPLETED
    ).order_by("-start_time").first()

    context = {
        "treatment_plans": treatment_plans,
        "assessment": assessment,
        "last_completed_initial_session": last_completed_initial_session,
    }

    return render(
        request,
        "patient/treatment_plan.html",
        context
    )


@login_required
def patient_treatment_plan_detail(request, plan_id):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect("main:home")

    patient = user.patient_profile

    treatment_plan = get_object_or_404(
        TreatmentPlan,
        id=plan_id,
        patient=patient
    )

    treatment_price = None

    if treatment_plan.status == TreatmentPlan.Status.DRAFT:
        treatment_price = calculate_treatment_price(
            treatment_plan.duration_weeks
        )

    context = {
        "treatment_plan": treatment_plan,
        "treatment_price": treatment_price,
    }

    return render(
        request,
        "patient/treatment_plan_detail.html",
        context
    )



@login_required
def patient_session_log(request):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect("main:home")

    patient = user.patient_profile

    sessions_qs = patient.sessions.select_related(
        "specialist", "specialist__user"
    ).order_by("-start_time")

    paginator = Paginator(sessions_qs, 10)
    page_number = request.GET.get("page")
    sessions = paginator.get_page(page_number)

    context = {
        "sessions": sessions,  
    }

    return render(
        request,
        "patient/session_log.html",
        context
    )



@login_required
def session_note_detail(request, session_id):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect("main:home")

    patient = user.patient_profile

    session = get_object_or_404(
        Session,
        id=session_id,
        patient=patient,
        status=Session.Status.COMPLETED
    )

    if not hasattr(session, "note"):
        messages.info(request, "لم يتم إضافة ملاحظات لهذه الجلسة بعد")
        return redirect("patient:session_log")

    context = {
        "session": session,
        "note": session.note,
    }

    return render(
        request,
        "patient/session_note_detail.html",
        context
    )

@login_required
def start_treatment_payment(request):
    user = request.user

    if user.role != User.Role.PATIENT:
        return redirect("main:home")

    patient = user.patient_profile

    plan_id = request.POST.get("plan_id")

    treatment_plan = get_object_or_404(
        TreatmentPlan,
        id=plan_id,
        patient=patient
    )

    if treatment_plan.status != TreatmentPlan.Status.DRAFT:
        return redirect("patient:treatment_plan")

    amount = calculate_treatment_price(
        treatment_plan.duration_weeks
    )
    

    Payment.objects.create(
        user=user,
        treatment_plan=treatment_plan,
        amount=amount,
        status="pending"
    )

    return redirect("payment:payment_page")
