from schedule import Scheduler
from django.conf import settings
import threading
import time
from results_mng.models import JobData
from token_queue_mng.models import Token
from token_queue_mng.services import TokenQueueService
from datetime import datetime, timedelta

def run_cleanup():
    print("Cleaning up...")
    target_date = datetime.now() - timedelta(hours=settings.CLEANUP_AFTER_HOURS)
    to_clean = JobData.objects.filter(date__lte=target_date)
    for data in to_clean:
        if (data.token.state == Token.TokenState.READY):
            TokenQueueService.set_token_expired(token.token)
        elif (data.token.state == Token.TokenState.SUBMITTED):
            TokenQueueService.set_token_cancelled(token.token)
        data.delete()


def run_continuously(self, interval=60):
    cease_continuous_run = threading.Event()
    class ScheduleThread(threading.Thread):
        @classmethod
        def run(cls):
            while not cease_continuous_run.is_set():
                self.run_pending()
                time.sleep(interval)
    continuous_thread = ScheduleThread()
    continuous_thread.setDaemon(True)
    continuous_thread.start()
    return cease_continuous_run

Scheduler.run_continuously = run_continuously

def start_cleanup_service():
    scheduler = Scheduler()
    scheduler.every(settings.RUN_CLEANUP_EVERY_HOURS).hours.do(run_cleanup)
    #scheduler.every().second.do(run_cleanup)
    scheduler.run_continuously()