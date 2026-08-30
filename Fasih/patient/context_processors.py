from treatment.models import TreatmentPlan


def patient_treatment_status(request):
    has_treatment_history = False

    if request.user.is_authenticated and request.user.role == "PATIENT":
        try:
            patient = request.user.patient_profile

            has_treatment_history = TreatmentPlan.objects.filter(
                patient=patient,
                status__in=[
                    TreatmentPlan.Status.ACTIVE,
                    TreatmentPlan.Status.COMPLETED,
                ]
            ).exists()

        except:
            pass

    return {
        "has_treatment_history": has_treatment_history
    }