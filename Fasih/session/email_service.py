from django.template.loader import render_to_string
from main.email_service import send_email


def send_session_confirmed_email(session):
    html = render_to_string(
        "session/emails/session_confirmed.html",
        {
            "patient_name": session.patient.user.get_full_name(),
            "specialist_name": session.specialist.user.get_full_name(),
            "date": session.start_time.date(),
            "time": session.start_time.time(),
        }
    )

    send_email(
        to=session.patient.user.email,
        subject="تم تأكيد جلستك | منصة فصيح",
        html_content=html
    )


def send_session_cancelled_email(session):
    html = render_to_string(
        "session/emails/session_cancelled.html",
        {
            "patient_name": session.patient.user.get_full_name(),
            "specialist_name": session.specialist.user.get_full_name(),
            "date": session.start_time.date(),
            "time": session.start_time.time(),
            "reason": session.patient_response_reason,
        }
    )

    send_email(
        to=session.patient.user.email,
        subject="تم إلغاء الجلسة | منصة فصيح",
        html_content=html
    )


def send_session_completed_email(session):
    html = render_to_string(
        "session/emails/session_completed.html",
        {
            "patient_name": session.patient.user.get_full_name(),
            "specialist_name": session.specialist.user.get_full_name(),
            "date": session.start_time.date(),
        }
    )

    send_email(
        to=session.patient.user.email,
        subject="تم انتهاء جلستك | منصة فصيح",
        html_content=html
    )


def send_session_rejected_email(session):
    html = render_to_string(
        "session/emails/session_rejected.html",
        {
            "patient_name": session.patient.user.get_full_name(),
            "specialist_name": session.specialist.user.get_full_name(),
            "date": session.start_time.date(),
            "time": session.start_time.time(),
            "reason": session.patient_response_reason,
        }
    )

    send_email(
        to=session.specialist.user.email,
        subject="تم رفض الجلسة المقترحة | منصة فصيح",
        html_content=html
    )