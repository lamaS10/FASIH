from .models import ChatRoom, Message

def unread_messages_processor(request):
    if request.user.is_authenticated:
        count = Message.objects.filter(
            room__in=ChatRoom.objects.filter(patient=request.user) | ChatRoom.objects.filter(specialist=request.user),
            is_read=False
        ).exclude(sender=request.user).count()
        
        return {'unread_messages_count': count}
    return {'unread_messages_count': 0}