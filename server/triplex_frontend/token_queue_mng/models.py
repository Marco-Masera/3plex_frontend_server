from django.db import models

class Token(models.Model):
    class TokenState(models.TextChoices):
        #Job has been submitted correctly
        SUBMITTED = 'Sb'
        READY = 'Rd'
        EXPIRED = 'Ex'
        CANCELLED = 'Cn'
        FAILED = 'Fl'

    token = models.AutoField(primary_key=True)
    _token_state = models.CharField(max_length=2, choices=TokenState.choices, default=TokenState.SUBMITTED,)
    
    @property
    def state(self) -> TokenState:
        return TokenState[self._token_state]
