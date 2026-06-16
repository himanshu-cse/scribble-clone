import json
from channels.generic.websocket import AsyncWebsocketConsumer

from chat.models import ChatMessage
from games.models import Game, Round
from games.services import process_guess, start_next_round
from rooms.models import Room

from channels.db import database_sync_to_async

@database_sync_to_async
def save_message(room_code, user, message):
    room = Room.objects.filter(code=room_code).first()
    return ChatMessage.objects.create(room=room, user=user, message=message)

@database_sync_to_async
def get_room(room_code):
    return Room.objects.filter(code=room_code).first()

@database_sync_to_async
def is_current_drawer(room, user):
    game = Game.objects.filter(room=room, status=Game.IN_PROGRESS).order_by("-created_at").first()
    if not game:
        return False
    
    current_round = Round.objects.filter(game=game).order_by("-round_number").first()
    if not current_round:
        return False
    
    return current_round.drawer == user

@database_sync_to_async
def start_next_round_for_room(room):
    game = Game.objects.filter(room=room, status=Game.IN_PROGRESS).order_by("-created_at").first()
    if not game:
        return

    current_round = Round.objects.filter(game=game).order_by("-round_number").first()
    if not current_round or not current_round.ended_at:
        return

    return start_next_round(game)

class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):

        # print("CONNECTED")

        self.room_code = self.scope["url_route"]["kwargs"]["room_code"]
        self.room_group_name = f"room_{self.room_code}"

        # Grab the user from the AuthMiddlewareStack
        self.user = self.scope["user"]

        # Fetch the room using database_sync_to_async
        self.room = await get_room(self.room_code)

        self.can_draw = await is_current_drawer(self.room, self.user)

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

        # print("MESSAGE RECEIVED")

        data = json.loads(text_data)
        event_type = data.get("type")

        # We handle the case where a user might not be logged in
        # AnonymousUser doesn't have a username, so we provide a fallback
        username = self.user.username if self.user.is_authenticated else "Anonymous"

        if event_type == "chat_message":
            message = data["message"]
            await save_message(self.room_code, self.user, message)
            # Wrap the heavily synchronous process_guess function
            is_correct_guess = await database_sync_to_async(process_guess)(self.room, self.user, message)

            if is_correct_guess:
                message = "correct_guess"

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "username": username,
                }
            )

        elif event_type == "draw":
            if not self.can_draw:
                return
            
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    "type": "draw_event",
                    "fromX": data["fromX"],
                    "fromY": data["fromY"],
                    "toX": data["toX"],
                    "toY": data["toY"],
                    "color": data.get("color", "#ff0000"),
                    "width": data.get("width", 5),
                }
            )

        elif event_type == "clear_canvas":
            if not self.can_draw:
                return

            await self.channel_layer.group_send(
                self.room_group_name, 
                {
                    "type": "clear_canvas_event",
                }
            )
        
        elif event_type == "start_next_round":
            await start_next_round_for_room(self.room)

    async def chat_message(self, event):
        # Extract the data from the broadcasted event
        message = event["message"]
        username = event["username"]

        # Send the finalized data to the frontend
        await self.send(
            text_data=json.dumps(
                {
                    "event": "chat_message",
                    "message": message,
                    "username": username,
                }
            )
        )

    async def system_message(self, event):
        # This catches the dictionary we sent from games/services.py
        # and sends it directly to the browser via WebSocket
        await self.send(text_data=json.dumps({
            "command": event["command"]
        }))

    async def draw_event(self, event):
        await self.send(text_data=json.dumps({
            "event": "draw",
            "fromX": event["fromX"],
            "fromY": event["fromY"],
            "toX": event["toX"],
            "toY": event["toY"],
            "color": event["color"],
            "width": event["width"],
        }))

    async def clear_canvas_event(self, event):
        await self.send(text_data=json.dumps({
            "event": "clear_canvas",
        }))