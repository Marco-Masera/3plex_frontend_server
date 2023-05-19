from token_queue_mng.models import *
from django.core.exceptions import ObjectDoesNotExist
from triplex_frontend.triplex_exceptions import TokenDoesNotExistException
from typing import Optional

class TokenQueueService:
    
    def get_new_token(name=None, email=None) -> Token:
        return Token.objects.create(job_name=name, email_address=email) 

    def find_token(token: str) -> Token:
        try:
            return Token.objects.get(token=token)
        except ObjectDoesNotExist:
            raise TokenDoesNotExistException()

    def get_tokens_by_email(email):
        return Token.objects.filter(email_address=email)
    
    def assert_token_ready(token: str):
        TokenQueueService.find_token(token).assert_state_ready()

    def token_is_state_submitted(token):
        return token.state == Token.TokenState.SUBMITTED
    
    def set_token_expired(token: str) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.EXPIRED) 
    
    def set_token_ready(token: str) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.READY) 
    
    def set_token_cancelled(token: str) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.CANCELLED) 
    
    def set_token_failed(token: str) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.FAILED) 
    
    def remove_token(token: str):
        Token.objects.filter(token=token).delete()
    
    def __set_token_state__(token: str, state: Token.TokenState) -> bool:
        try:
            token = Token.objects.get(token=token)
            token._token_state = state
            token.save()
            return True
        except ObjectDoesNotExist:
            return False

