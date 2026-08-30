import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from .models import ChatRoom, Message

User = get_user_model()


@login_required
def chat_inbox(request):
    user = request.user
    
    rooms = (ChatRoom.objects.filter(patient=user) | ChatRoom.objects.filter(specialist=user)).distinct().order_by('-created_at')

    if not rooms.exists():
        patient_profile = getattr(user, 'patient_profile', None) or getattr(user, 'patient', None)
        if patient_profile:
            specialist = getattr(patient_profile, 'specialist', None) or getattr(patient_profile, 'assigned_specialist', None)
            if specialist:
                specialist_user = specialist.user if hasattr(specialist, 'user') else specialist
                room, _ = ChatRoom.objects.get_or_create(patient=user, specialist=specialist_user)
                return redirect('chat_room', room_id=room.id)

    return render(request, 'chat/inbox.html', {'rooms': rooms})


@login_required
def start_chat(request, patient_id):
    from patient.models import Patient

    patient_obj = get_object_or_404(Patient, id=patient_id)
    patient_user = patient_obj.user

    specialist_user = request.user

    room, created = ChatRoom.objects.get_or_create(
        patient=patient_user,
        specialist=specialist_user
    )

    return redirect('chat_room', room_id=room.id)


@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if request.user != room.patient and request.user != room.specialist:
        return redirect('chat_inbox')

    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    messages = room.messages.order_by('timestamp')
    other_user = room.specialist if request.user == room.patient else room.patient

    return render(request, 'chat/room.html', {
        'room': room,
        'chat_messages': messages,
        'other_user': other_user,
    })


@login_required
def send_message(request, room_id):
    if request.method == 'POST':
        room = get_object_or_404(ChatRoom, id=room_id)
        content = None

        if request.content_type == 'application/json':
            try:
                data = json.loads(request.body)
                content = data.get('content') or data.get('message')
            except json.JSONDecodeError:
                pass
        else:
            content = request.POST.get('content') or request.POST.get('message')

        if content and content.strip():
            message = Message.objects.create(
                room=room,
                sender=request.user,
                content=content.strip()
            )
            return JsonResponse({
                'status': 'ok',
                'message_id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M')
            })

    return JsonResponse({'status': 'error', 'message': 'محتوى الرسالة فارغ أو الطلب غير صحيح'}, status=400)