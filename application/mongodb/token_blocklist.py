from mongoengine import Document, StringField

class TokenBlocklist(Document):
    jti = StringField(required=True)

    meta = {
        'indexes': [
            {'fields': ['jti'], 'unique': True}
        ]
    }