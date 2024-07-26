from mongoengine import ReferenceField, BooleanField, StringField

from application.mongodb.base_document import BaseDocument
from application.mongodb.user import User

class Message(BaseDocument):
	content = StringField()
	user = ReferenceField(User)
	is_response = BooleanField(default=False)