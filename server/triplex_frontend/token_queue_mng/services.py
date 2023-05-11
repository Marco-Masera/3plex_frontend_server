from token_queue_mng.models import *
from django.core.exceptions import ObjectDoesNotExist
from typing import Optional

class TokenQueueService:
    def get_new_token() -> Token:
        return Token.objects.create() 

    def find_token(token: int) -> Optional[Token]:
        try:
            return Token.objects.get(token=token)
        except ObjectDoesNotExist:
            return None
    
    def set_token_expired(token: int) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.EXPIRED) 
    
    def set_token_cancelled(token: int) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.CANCELLED) 
    
    def set_token_failed(token: int) -> bool:
        return TokenQueueService.__set_token_state__(token, Token.TokenState.FAILED) 
    
    def remove_token(token: int):
        Token.objects.filter(token=token).delete()
    
    def __set_token_state__(token: int, state: Token.TokenState) -> bool:
        try:
            token = Token.objects.get(token=token)
            token._token_state = state 
            token.save()
            return True
        except ObjectDoesNotExist:
            return False

