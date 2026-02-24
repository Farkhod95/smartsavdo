import json
from channels.generic.websocket import AsyncWebsocketConsumer


class WSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")

        # user login bo'lmagan bo'lsa - ulanishni rad qilamiz
        if not user or user.is_anonymous:
            await self.close(code=4001)
            return

        self.group_name = f"notes_user_{user.id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

        # xohlasangiz connect bo'lganda test xabar
        # await self.send(text_data=json.dumps({"type": "connected", "user_id": user.id}))

    async def disconnect(self, close_code):
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def note_event(self, event):
        payload = event.get("payload", {})
        await self.send(text_data=json.dumps({
            "type": "note_event",
            "payload": payload
        }))