from token_queue_mng.models import *
from django.core.exceptions import ObjectDoesNotExist
from triplex_frontend.triplex_exceptions import TokenDoesNotExistException
from typing import Optional

class TokenQueueService:
    
    def get_new_token(name=None, email=None, jobData = None) -> Token:
        return Token.objects.create(job_name=name, email_address=email, job = jobData) 

    def find_token(token: str) -> Token:
        try:
            return Token.objects.get(token=token)
        except ObjectDoesNotExist:
            raise TokenDoesNotExistException()

    def get_tokens_by_email(email):
        return Token.objects.filter(email_address=email)
    
    def check_token_ready(token: str):
        TokenQueueService.find_token(token).check_state_ready()

    def token_is_state_submitted(token):
        return token.state == "Submitted"
    
    def remove_token(token: str):
        Token.objects.filter(token=token).delete()

    def get_tokens_by_job(job):
        return Token.objects.filter(job=job)

