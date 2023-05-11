from django.db import models

class Token(models.model):
    class TokenState(models.TextChoices):
        #Job has been submitted correctly
        SUBMITTED = 'Sb', _('Submitted')
        READY = 'Rd', _('Ready')
        EXPIRED = 'Ex', _('Expired')
        CANCELLED = 'Cn', _('Cancelled')
        FAILED = 'Fl', _('Failed')

    token = models.AutoField()
    _token_state_ = models.CharField(max_length=2, choices=TokenState.choices, default=TokenState.SUBMITTED,)
    
    @property
    def state(self) -> TokenState:
        return TokenState[self._token_state_]
