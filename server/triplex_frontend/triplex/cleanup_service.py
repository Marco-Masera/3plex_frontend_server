from schedule import Scheduler
from django.conf import settings
import threading
import time
from results_mng.models import JobData
from results_mng.services import ResultsMngServices
from datetime import datetime, timedelta

def run_cleanup():
    print("Cleaning up...")
    target_date = datetime.now() - timedelta(hours=settings.CLEANUP_AFTER_HOURS)
    ResultsMngServices.cleanup_old_jobs(target_date)


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
    print("Starting cleanup service")
    scheduler = Scheduler()
    scheduler.every(settings.RUN_CLEANUP_EVERY_HOURS).hours.do(run_cleanup)
    #scheduler.every().second.do(run_cleanup)
    scheduler.run_continuously()