from django.db import models
from triplex_frontend.triplex_exceptions import *
from django.db import IntegrityError
import secrets 
import datetime
from results_mng.models import JobData
from django.forms import model_to_dict
from promoter_stability_test.models import *

def generate_random_alphanumeric(length) -> str:
    return secrets.token_urlsafe(length).replace("/","_").replace(" ", "").replace("\t", "").replace("-", "_")

class Token(models.Model):
    token = models.CharField(max_length=64, blank=False, editable=False, unique=True, primary_key=True)
    submission_date = models.DateTimeField(auto_now_add=True, auto_now=False)
    job_name = models.CharField(max_length=64, null=True, default=None)
    email_address = models.EmailField(max_length=254, null=True, default=None)
    standard_job = models.ForeignKey(JobData, on_delete=models.CASCADE, null=True)
    promoter_stability_test_job = models.ForeignKey(StabilityTestJobData, on_delete=models.CASCADE, null=True)
    @property
    def type_of_job(self):
        if (self.standard_job is not None):
            return "standard"
        elif (self.promoter_stability_test_job is not None):
            return "promoter_stability_test"
        else:
            return "None"

    @property
    def job(self):
        if (self.type_of_job == "standard"):
            return self.standard_job
        else:
            return self.promoter_stability_test_job

    def __str__(self):
        return f"{self.submission_date} - {self.job_name} - {self.token} - {self.job.state}"

    @property
    def species(self):
        return self.job.species

    @property
    def state(self) -> str:
        return self.job.state
    @property
    def ssRNA_id(self) -> str:
        if (self.job.ssRNA_id is not None):
            return self.job.ssRNA_id.id
        return None
    
    @property
    def submission_date_formatted(self) -> str:
        return self.submission_date.strftime("%d-%m-%Y %H:%M:%S")

    def to_dict(self):
        dict_ = model_to_dict(self)
        dict_["state"] = self.state
        dict_["token"] = self.token
        dict_["date"] =  self.submission_date.strftime("%d-%m-%Y %H:%M:%S")
        dict_["ssRNA_id"] = self.ssRNA_id
        dict_["species"] = self.species
        dict_["type_of_job"] = self.type_of_job
        dict_["have_visualization"] = self.job.have_visualization
        return dict_

    def assert_state_expired(self):
        if not (self.state == "Expired"):
            raise JobFailedException()

    def assert_state_ready(self):
        if (self.state == "Ready"):
            return
        if (self.state == "Submitted"):
            raise DataNotReadyYetException()
        if (self.state == "Expired"):
            raise DataExpiredException()
        if (self.state == "Cancelled"):
            raise JobCancelledException()
        if (self.state == "Failed"):
            raise JobFailedException()

    def assert_state_submitted(self):
        if (self.state != "Submitted"):
            raise TokenIsNotStateSubmittedException()
    
    def assert_type_standard(self):
        if (self.type_of_job != "standard"):
            raise JobNotStandardException()
    def assert_type_promoter_test(self):
        if (self.type_of_job != "promoter_stability_test"):
            raise JobNotStandardException()

    def check_state_ready(self):
        return self.state == "Ready"
    
    def check_state_failed(self):
        return self.state == "Failed"
    
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


class DBD(models.Model):
    token = models.ForeignKey(Token, null=False, blank=False, on_delete=models.CASCADE)
    start = models.IntegerField(null=False, blank=False)
    end = models.IntegerField(null=False, blank=False)