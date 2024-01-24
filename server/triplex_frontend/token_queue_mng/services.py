from token_queue_mng.models import *
from promoter_stability_test.models import StabilityTestJobData
from django.core.exceptions import ObjectDoesNotExist
from triplex_frontend.triplex_exceptions import TokenDoesNotExistException
from promoter_stability_test.services import PromoterStabilityTestServices
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from results_mng.services import ResultsMngServices

class TokenQueueService:
    
    def get_new_token(name=None, email=None, jobData = None) -> Token:
        if (isinstance(jobData, JobData)):
            return Token.objects.create(job_name=name, email_address=email, standard_job = jobData)
        elif (isinstance(jobData, StabilityTestJobData)):
            return Token.objects.create(job_name=name, email_address=email, promoter_stability_test_job = jobData)
        

    def find_token(token: str) -> Token:
        try:
            return Token.objects.get(token=token)
        except ObjectDoesNotExist:
            raise TokenDoesNotExistException()

    def update_token_email(token: str, email: str):
        token_obj = TokenQueueService.find_token(token)
        token_obj.email_address = email 
        token_obj.save()

    def get_tokens_by_email(email):
        return Token.objects.filter(email_address=email).order_by('-submission_date')
    
    def check_token_ready(token: str):
        TokenQueueService.find_token(token).check_state_ready()
    
    def remove_token(token: str):
        Token.objects.filter(token=token).delete()

    def get_tokens_by_job(job):
        #TODO compatibility with other types of jobs
        if (isinstance(job, JobData)):
            return Token.objects.filter(standard_job=job)
        if (isinstance(job, StabilityTestJobData)):
            return Token.objects.filter(promoter_stability_test_job=job)
        return []

    #Delete data object if no token exists associated to it (mostly for exception handling)
    def delete_data_if_orphan(jobData):
        if (len(TokenQueueService.get_tokens_by_job(jobData))==0):
            jobData.delete()

    def notify_user_email_job_completed(token: Token):
        if (token.email_address is None):
            return
        if (token.job_name is not None):
            message = f"Hi.\nYour job with token {token.token} and name {token.job_name}, sent on {token.submission_date_formatted}, is completed."
        else:
            message = f"Hi.\nYour job with token {token.token}, sent on {token.submission_date_formatted}, is completed."
        message = message + f"\nYou can check it at: {settings.CLIENT_URL}checkjob/token/{token.token}"
        send_mail(
            "3plex: your job is completed",
            message,
            settings.EMAIL_HOST_USER,
            [token.email_address],
            fail_silently=False,
        )
    
    def notify_user_email_job_failed(token: Token):
        if (token.email_address is None):
            return
        if (token.job_name is not None):
            message = f"Hi.\nYour job with token {token.token} and name {token.job_name}, sent on {token.submission_date_formatted}, has failed."
        else:
            message = f"Hi.\nYour job with token {token.token}, sent on {token.submission_date_formatted}, has failed."
        message = message + f"\nYou can check it at: {settings.CLIENT_URL}checkjob/token/{token.token}"
        send_mail(
            "3plex: your job failed",
            message,
            settings.EMAIL_HOST_USER,
            [token.email_address],
            fail_silently=False,
        )

    def notify_all_users_email_job_completed(job):
        users = TokenQueueService.get_tokens_by_job(job)
        for user in users:
            TokenQueueService.notify_user_email_job_completed(user)

    def notify_all_users_email_job_failed(job):
        users = TokenQueueService.get_tokens_by_job(job)
        for user in users:
            TokenQueueService.notify_user_email_job_failed(user)
        

    def set_dbds(token: Token, dbds):
         DBD.objects.filter(token=token).delete()
         for dbd in dbds:
            DBD.objects.create(token=token, start=dbd[0], end=dbd[1])
    
    def get_dbds(token: Token):
        dbds = DBD.objects.filter(token=token).order_by('start')
        return [ [dbd.start, dbd.end] for dbd in dbds ]

    def send_mail_with_all_jobs(email: str):
        tokens = Token.objects.filter(email_address=email).order_by('-submission_date')
        if (len(tokens)==0):
            return 
        #divide tokens between states
        divided_tokens = {}
        for token in tokens:
            if (not token.state in divided_tokens):
                divided_tokens[token.state] = []
            divided_tokens[token.state].append(token)
        #format each one: name, state, link
        formatted_tokens = {}
        for state in divided_tokens.keys():
            formatted_tokens[state] = []
            for token in divided_tokens[state]:
                job_name = token.job_name
                if (job_name is None):
                    job_name = "N/A"
                formatted_tokens[state].append(f"Name: {job_name} - submitted: {token.submission_date} - URL: {settings.CLIENT_URL}checkjob/token/{token.token}")
        #send email
        message = "3plex: your jobs list:\n"
        states = ["Submitted", "Ready", "Expired", "Failed"]
        for state in states:
            if (state in formatted_tokens):
                message += f"\n{state}:\n"
                for string in formatted_tokens[state]:
                    message += f"{string}\n"
        send_mail(
            "3plex: all your jobs",
            message,
            settings.EMAIL_HOST_USER,
            [email],
            fail_silently=False,
        )

    def getDataFromToken(token: Token):
        #TODO implement for other type of jobs
        if (token.type_of_job == "standard"):
            if (token.check_state_ready() or token.check_state_failed()):
                data = ResultsMngServices.get_data(token.job)
                params = ResultsMngServices.get_triplex_params(token.job)
                ResultsMngServices.update_data_last_date(token.job)
            else:
                data = {}
                params = ResultsMngServices.get_triplex_params(token.job)
        elif (token.type_of_job == "promoter_stability_test"):
            if (token.check_state_ready() or token.check_state_failed()):
                data = PromoterStabilityTestServices.get_data(token.job)
                params = PromoterStabilityTestServices.get_triplex_params(token.job)
                PromoterStabilityTestServices.update_data_last_date(token.job)
            else:
                data = {}
                params = PromoterStabilityTestServices.get_triplex_params(token.job)
        else:
            data = {}
            params = {}
        return data, params