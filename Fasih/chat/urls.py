from django.urls import path
from . import views
urlpatterns = [
    path('', views.chat_inbox, name='chat_inbox'),
    path('<int:room_id>/', views.chat_room, name='chat_room'),
    path('start/<int:patient_id>/', views.start_chat, name='start_chat'),
    path('send/<int:room_id>/', views.send_message, name='send_message'),
]