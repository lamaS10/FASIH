import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import ChatRoom, Message

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_content = text_data_json['message']
        user = self.scope['user']

        if user.is_authenticated and message_content.strip():
            msg = await self.save_message(user, message_content)

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': msg.content,
                    'sender_name': user.get_full_name() or user.username,
                    'sender_id': user.id,
                    'timestamp': msg.timestamp.strftime("%I:%M %p")
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'message': event['message'],
            'sender_name': event['sender_name'],
            'sender_id': event['sender_id'],
            'timestamp': event['timestamp']
        }))

    @database_sync_to_async
    def save_message(self, user, content):
        room = ChatRoom.objects.get(id=self.room_id)
        return Message.objects.create(room=room, sender=user, content=content)