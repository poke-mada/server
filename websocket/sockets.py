import json

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

    async def receive(self, text_data=None, **kwargs):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if message['type'] == 'request_data':
            streamer = message['streamer']

            await self.channel_layer.group_send(
                self.room_group_name, {"type": "chat.message", "message": json.dumps(data)}
            )
            return


        await self.channel_layer.group_send(
            self.room_group_name, {"type": "chat.message", "message": message}
        )

    # Receive message from room group
    async def chat_message(self, event):
        print(event)
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))


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
        print(event)
        message = event["message"]

        # Send message to WebSocket
        await self.send(text_data=json.dumps({"message": message}))
