import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer


class OverlayConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"chat_{self.room_name}"
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    @classmethod
    def get_trainer(cls, streamer_name):
        from event_api.models import MastersProfile
        profile: MastersProfile = MastersProfile.objects.filter(
            user__username__exact=streamer_name,
            user__masters_profile__profile_type=MastersProfile.TRAINER
        ).first()

        return profile.trainer

    @classmethod
    def serialize(cls, trainer):
        from websocket.serializers import OverlaySerializer
        serializer = OverlaySerializer(trainer)
        return serializer.data

    async def receive(self, text_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        if text_data_json['type'] == 'request_data':
            streamer_name = text_data_json['streamer']
            trainer = await sync_to_async(OverlayConsumer.get_trainer)(streamer_name)
            data = await sync_to_async(OverlayConsumer.serialize)(trainer)
            new_message = json.dumps(dict(context='pokemon_data', **data))

            await self.channel_layer.group_send(
                self.room_group_name,
                {"type": "chat.message", "message": new_message}
            )
            return
        message = text_data_json["message"]

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    @classmethod
    def send_overlay_data(cls, streamer_name):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        trainer = OverlayConsumer.get_trainer(streamer_name)
        data = OverlayConsumer.serialize(trainer)
        new_message = json.dumps(dict(context='pokemon_data', **data))

        async_to_sync(channel_layer.group_send)(
            f'chat_{streamer_name}',
            {"type": "chat.message", "message": new_message}
        )


class DataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"data_{self.room_name}"
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))

    @classmethod
    def send_custom_data(cls, streamer_name, new_message):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        new_message = json.dumps(new_message)

        async_to_sync(channel_layer.group_send)(
            f'data_{streamer_name}',
            {"type": "chat.message", "message": new_message}
        )


class GameDataConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
        self.room_group_name = f"game_data_{self.room_name}"
        # Join room group
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, **kwargs):
        text_data_json = json.loads(text_data)

        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": text_data_json}
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event["message"]
        await self.send(text_data=json.dumps({"message": message}))

    @classmethod
    def send_custom_data(cls, streamer_name, new_message):
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        new_message = json.dumps(new_message)

        async_to_sync(channel_layer.group_send)(
            f'game_data_{streamer_name}',
            {"type": "chat.message", "message": new_message}
        )
