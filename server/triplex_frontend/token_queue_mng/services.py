from token_queue_mng.models import *
from promoter_stability_test.models import StabilityTestJobData
from django.core.exceptions import ObjectDoesNotExist
from triplex_frontend.triplex_exceptions import TokenDoesNotExistException,JobFailedException,HashDoesNotBatchException
from promoter_stability_test.services import PromoterStabilityTestServices
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from results_mng.services import ResultsMngServices
import tarfile
import os.path
import hashlib

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
            message = f"3plex Web: your Job named {token.job_name} is completed.\n\n"
        else:
            message = f"3plex Web: your anonymous Job is completed.\n\n"
        message += f"Job details:\nToken: {token.token}\n"
        message += f"Submission date: {token.submission_date_formatted}\n"
        message += f"\nAccess your job's results: {settings.CLIENT_URL}checkjob/token/{token.token}\n\n"
        message += "Cite 3plex Web:\n"
        message += "Masera, Marco & Cicconetti, Chiara & Ferrero, Francesca & Oliviero, Salvatore & Molineris, Ivan. (2025). 3plex Web: An Interactive Platform for RNA:DNA Triplex Prediction and Analysis. 10.48550/arXiv.2504.18076.\n\n"
        
        message += "You are receiving this notification because you set this email address during job submission. "
        message += "If you did not use 3plex Web please ignore this email. You will not receive other emails related to this job."
        try:
            send_mail(
                "3plex: job completed",
                message,
                settings.EMAIL_HOST_USER,
                [token.email_address],
                fail_silently=False,
            )
        except Exception as e:
            try:
                send_mail(
                    "3plex, problem with mail",
                    f"Original msg:\n{message} - receiver: {token.email_address}",
                    settings.EMAIL_HOST_USER,
                    [marco.masera@unito.it],
                    fail_silently=False,
                )
            except Exception as e:
                pass
    
    def notify_user_email_job_failed(token: Token):
        if (token.email_address is None):
            return
        if (token.job_name is not None):
            message = f"3plex Web: your Job named {token.job_name} has failed to complete.\n\n"
        else:
            message = f"3plex Web: your anonymous Job has failed to complete.\n\n"
        message += f"Job details:\nToken: {token.token}\n"
        message += f"Submission date: {token.submission_date_formatted}\n"
        message += "More details about the reson for failure can be found in the Job's logs.\n"
        message += f"\nAccess your job's details: {settings.CLIENT_URL}checkjob/token/{token.token}\n\n" 
        message += "You are receiving this email because you set this email address during job submission. "
        message += "If you did not use 3plex Web please ignore this email. You will not receive other mails related to this job."
        send_mail(
            "3plex: job failed",
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

    def export_job_data(token):
        token.assert_state_ready()
        if (token.job.export_hash is not None and len(token.job.export_hash)>0 and bool(token.job.export_tarball)):
            return token.job.export_tarball.url
        source_dir = os.path.join(settings.MEDIA_ROOT, "jobs", token.job.base_path)
        output_filename = os.path.join(settings.MEDIA_ROOT, "jobs", f"export_{token.job.base_path}.tar.gz")
        with tarfile.open(output_filename, "w:gz") as tar:
            tar.add(source_dir, arcname=os.path.basename(source_dir))
        #Generate hash of tarball
        h = hashlib.sha1() #Doesn't need crittographic hashing function
        with open(output_filename,'rb') as f: 
            while chunk := f.read(128*h.block_size): 
                h.update(chunk)
        hashed = h.hexdigest()
        if (len(hashed) > 128):
            hashed = hashed[:128]
        #Set file in jobData
        token.job.set_export_file(f"jobs/export_{token.job.base_path}.tar.gz", hashed)
        return token.job.export_tarball.url

    def import_job_data(token, file):
        token.assert_state_expired()
        if (token.job.export_hash is None or len(token.job.export_hash)==0 or token.job.cleaned_up==False):
            raise JobFailedException()
        #Generate hash of file
        h = hashlib.sha1() #Doesn't need crittographic hashing function
        with open(file,'rb') as f: 
            while chunk := f.read(128*h.block_size): 
                h.update(chunk)
        hashed = h.hexdigest()
        if (len(hashed) > 128):
            hashed = hashed[:128]
        if not (hashed == token.job.export_hash):
            raise HashDoesNotBatchException()
        #Extract the tarball into the directory
        with tarfile.open(file, "r:gz") as tar:
            tar.extractall(path=os.path.join(settings.MEDIA_ROOT_ABS_PATH,"jobs"))
        #Remove "file"
        #Set job back to ready
        token.job.cleaned_up = False
        token.job.state = "Ready"
        token.job.save()
