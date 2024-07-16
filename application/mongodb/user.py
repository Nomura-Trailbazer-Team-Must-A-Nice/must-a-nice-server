from mongoengine import StringField, ValidationError
from email_validator import validate_email, EmailNotValidError

from application.mongodb.base_document import BaseDocument

class User(BaseDocument):
    email = StringField(unique=True, required=True)
    first_name = StringField(required=True)
    last_name = StringField()

    def validate(self, clean=True):
        input_email = self.email
        try:
            email_info = validate_email(self.email, check_deliverability=False)
            self.email = email_info.normalized
        except EmailNotValidError as exc:
            raise ValidationError(f"Invalid email address '{input_email}'") from exc
        return super().validate(clean)