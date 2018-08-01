import asyncio
import json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

from .models import Thread, ChatMessage

class ChatConsumer(AsyncConsumer):

	async def websocket_connect(self, event):
		print("connected",event)
		
		other_user = self.scope['url_route']['kwargs']['username']
		me = self.scope['user']
		#print(other_user,me) 
		thread_obj = await self.get_thread(me, other_user)

		#print(me,thread_obj.id)
		self.thread_obj = thread_obj
		chat_room = f"thread_{thread_obj.id}"
		self.chat_room = chat_room
		await self.channel_layer.group_add(
			chat_room,
			self.channel_name #default attribute of channels
		)

		await self.send({
			"type": "websocket.accept"
		})

	async def websocket_receive(self, event):
		print("receive",event)
		front_text = event.get('text', None)
		if front_text is not None:
			loaded_dict_data = json.loads(front_text) 
			msg = loaded_dict_data.get('message')
			print(msg)
			user =  self.scope['user']
			username = 'default'
			if user.is_authenticated:
				username = user.username
				await self.create_chat_message(user, msg)

			myResponse = {
				'message' : msg,
				'username' : username
			}
			
			#brodcast the actual message event to be sent
			print('group_send')
			#try:
			print('self.channel_layer',self.chat_room)
			await self.channel_layer.group_send(
				self.chat_room,
				{
					"type": "chat_message",
					"text" : json.dumps(myResponse)
				}
				
			)
			#except Exception as e:
			#print('group_send_exception',e)
			# await self.send({
			# "type": "websocket.send",
			# "text": json.dumps(myResponse)
			# })
	async def chat_message(self, event):
		#print('message', event)
		#send the actual message
		await self.send({
			"type": "websocket.send",
			"text": event['text'] 
		})
				

	async def websocket_disconnect(self, event):
		print("disconnect",event)

	

	@database_sync_to_async
	def get_thread(self, user, other_username):
		return Thread.objects.get_or_new(user, other_username)[0]

	@database_sync_to_async
	def create_chat_message(self, me, msg):
		thread_obj = self.thread_obj
		return ChatMessage.objects.create(thread=thread_obj, user=me, message=msg)