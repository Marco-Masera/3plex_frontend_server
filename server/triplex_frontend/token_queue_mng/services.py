from token_queue_mng.models import *
from django.core.exceptions import ObjectDoesNotExist
from triplex_frontend.triplex_exceptions import TokenDoesNotExistException
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings

class TokenQueueService:
    
    def get_new_token(name=None, email=None, jobData = None) -> Token:
        return Token.objects.create(job_name=name, email_address=email, standard_job = jobData) 

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

    def token_is_state_submitted(token):
        return token.state == "Submitted"
    
    def remove_token(token: str):
        Token.objects.filter(token=token).delete()

    def get_tokens_by_job(job):
        return Token.objects.filter(standard_job=job)

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