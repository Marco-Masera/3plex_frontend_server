from django.db import models
from triplex_frontend.triplex_exceptions import JobFailedException, JobCancelledException,DataExpiredException,DataNotReadyYetException
from django.db import IntegrityError
import secrets 

def generate_random_alphanumeric(length) -> str:
    return secrets.token_urlsafe(32).replace("/","_").replace(" ", "").replace("\t", "")

class Token(models.Model):
    class TokenState(models.TextChoices):
        #Job has been submitted correctly
        SUBMITTED = 'Sb'
        READY = 'Rd'
        EXPIRED = 'Ex'
        CANCELLED = 'Cn'
        FAILED = 'Fl'

    token = models.CharField(max_length=32, blank=False, editable=False, unique=True, primary_key=True)
    _token_state = models.CharField(max_length=2, choices=TokenState.choices, default=TokenState.SUBMITTED,)
    
    @property
    def state(self) -> TokenState:
        return Token.TokenState(self._token_state)

    def assert_state_ready(self):
        if (self.state == Token.TokenState.READY):
            return
        if (self.state == Token.TokenState.SUBMITTED):
            raise DataNotReadyYetException()
        if (self.state == Token.TokenState.EXPIRED):
            raise DataExpiredException()
        if (self.state == Token.TokenState.CANCELLED):
            raise JobCancelledException()
        if (self.state == Token.TokenState.FAILED):
            raise JobFailedException()
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = generate_random_alphanumeric(32)
            # using your function as above or anything else
            failures = 0
            while True:
                try:
                    super(Token, self).save(*args, **kwargs)
                except IntegrityError:
                    failures += 1
                    if failures > 5: # or some other arbitrary cutoff point at which things are clearly wrong
                        raise Exception()
                    else:
                        self.auto_pseudoid = generate_random_alphanumeric(32)
                        break
        else:
            super(Token, self).save(*args, **kwargs)