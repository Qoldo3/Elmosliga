import threading
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.tokens import default_token_generator
import logging
logger = logging.getLogger(__name__)

class EmailThread(threading.Thread):
    def __init__(self, email_obj):
        super().__init__(daemon=True)
        self.email_obj = email_obj

    def run(self):
        try:
            logger.info(f"Attempting to send email to: {self.email_obj.to}")
            self.email_obj.send()
            logger.info(f"Email sent successfully to: {self.email_obj.to}")
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            logger.exception(e)
