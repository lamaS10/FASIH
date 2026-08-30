from django.shortcuts import render, redirect, get_object_or_404
from .models import TreatmentPlan, ShortTermGoal, ProgressReport, DailyPlan, DailyTask
from patient.models import Patient
from specialist.models import Specialist
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.contrib import messages
from datetime import timedelta, datetime
from django.core.paginator import Paginator



@login_required
def treatment_patients(request):
    specialist = get_object_or_404(Specialist, user=request.user)

    patients = Patient.objects.filter(
        assessments__specialist=specialist,
        assessments__status='ACCEPTED'
    ).distinct()

    patient_plans = []

    for patient in patients:
        plan = TreatmentPlan.objects.filter(
            patient=patient,
            specialist=specialist
        ).order_by("-created_at").first()

        if plan:
            plan.update_status_if_expired()

        patient_plans.append({"patient": patient,"plan": plan })
    return render(
        request,
        "treatment/treatment_patients.html",
        {
            "patient_plans": patient_plans
        }
    )


@login_required
def create_treatment_plan(request, file_number):
    patient = get_object_or_404(Patient, file_number=file_number)
    specialist = get_object_or_404(Specialist, user=request.user)

    if request.method == "POST":
        start_date = datetime.strptime(
            request.POST.get("start_date"),
            "%Y-%m-%d"
        ).date()

        plan = TreatmentPlan.objects.create(
            patient=patient,
            specialist=specialist,
            diagnosis=request.POST.get("diagnosis"),
            problem_description=request.POST.get("problem_description"),
            start_date=start_date,                     
            duration_weeks=int(request.POST.get("duration_weeks")),
            sessions_per_week=request.POST.get("sessions_per_week") or None,
            session_duration_minutes=request.POST.get("session_duration_minutes") or None,
            status=TreatmentPlan.Status.DRAFT
        )

        total_days = plan.duration_weeks * 7

        for i in range(total_days):
            current_date = start_date + timedelta(days=i)
            DailyPlan.objects.create(
                treatment_plan=plan,
                date=current_date,
                day_name=current_date.strftime("%A")
            )

        return redirect(
            "treatment:treatment_plan_detail",
            plan_id=plan.id
        )

    return render(
        request,
        "treatment/create_treatment_plan.html",
        {"patient": patient}
    )



@login_required
def treatment_plan_detail(request, plan_id):
    treatment_plan = get_object_or_404(TreatmentPlan, id=plan_id)

    days = DailyPlan.objects.filter(
        treatment_plan=treatment_plan
    ).order_by("date")

    paginator = Paginator(days, 7)

    page_number = request.GET.get("page")
    daily_plans = paginator.get_page(page_number)

    return render(
        request,
        "treatment/treatment_plan_detail.html",
        {
            "plan": treatment_plan,
            "daily_plans": daily_plans,
        }
    )

@login_required
def add_short_term_goal(request, plan_id):
    print("METHOD:", request.method)
    print("POST DATA:", request.POST)

    treatment_plan = get_object_or_404(TreatmentPlan, id=plan_id)
    

    if request.method == "POST":
       
        print(request.POST)
        ShortTermGoal.objects.create(
            treatment_plan=treatment_plan,
            description=request.POST.get("description"),
            target_accuracy=request.POST.get("target_accuracy")
        )
        messages.success(request, "تمت إضافة الهدف العلاجي بنجاح")
        return redirect("treatment:treatment_plan_detail", plan_id=plan_id)

    return render(request, "treatment/add_short_term_goal.html", {
        "plan": treatment_plan
    })


@login_required
def edit_daily_task(request, task_id):
    task = get_object_or_404(DailyTask, id=task_id)

    if request.method == "POST":
        task.task_name = request.POST.get("task_name")
        task.target_letter = request.POST.get("target_letter")
      
        task.save()
        messages.success(request, "تم تعديل المهمة بنجاح")

        return redirect(
            "treatment:treatment_plan_detail",
            plan_id=task.daily_plan.treatment_plan.id
        )

    return render(request, "treatment/edit_daily_task.html", {
        "task": task
    })



@login_required
def add_daily_task(request, day_id):
    day = get_object_or_404(DailyPlan, id=day_id)

    if request.method == "POST":
        DailyTask.objects.create(
            daily_plan=day,
            task_name=request.POST.get("task_name"),
            target_letter=request.POST.get("target_letter")
        )
        messages.success(request, "تمت إضافة المهمة بنجاح")
        return redirect(
            "treatment:treatment_plan_detail",
            plan_id=day.treatment_plan.id
        )

    return render(request, "treatment/add_daily_task.html", {
        "day": day
    })


@login_required
def view_task_execution(request, task_id):
    task = get_object_or_404(DailyTask, id=task_id)
    specialist = get_object_or_404(Specialist, user=request.user)

   
    if task.daily_plan.treatment_plan.specialist != specialist:
        return HttpResponseForbidden("غير مصرح لك")

 
    if request.method == "POST":
        notes = request.POST.get("specialist_notes", "").strip()
        task.specialist_notes = notes
        task.save()

        messages.success(request, "تم حفظ ملاحظات الأخصائي بنجاح")

        return redirect(
            "treatment:view_task_execution",
            task_id=task.id
        )

    return render(
        request,
        "treatment/task_execution_view.html",
        {"task": task}
    )

