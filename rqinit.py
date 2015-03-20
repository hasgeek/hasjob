from urlparse import urlparse

from hasjob import init_for, app

from redis import Redis

import rq

init_for('production')
REDIS_URL = app.config.get('REDIS_URL', 'redis://localhost:6379/0')

# REDIS_URL is not taken by setup_default_arguments function of rq/scripts/__init__.py
# so, parse that into pieces and give it

r = urlparse(REDIS_URL)
REDIS_HOST = r.hostname
REDIS_PORT = r.port
REDIS_PASSWORD = r.password
REDIS_DB = 0


MAX_FAILURES = 3

queues = None


def error_handler(job, exc_type, exc_value, traceback):
    job.meta.setdefault('failures', 0)
    job.meta['failures'] += 1

    # Too many failures
    if job.meta['failures'] >= MAX_FAILURES:
        app.logger.error('job %s: failed too many times times - moving to failed queue' % job.id)
        job.save()
        return True

    # Requeue job and stop it from being moved into the failed queue
    for queue in queues:
        if queue.name == job.origin:
            queue.enqueue_job(job)
            return False

    # Can't find queue, which should basically never happen as we only work jobs that match the given queue names and
    # queues are transient in rq.
    return True


with rq.Connection():
    queues = [rq.Queue("hasjob", connection=Redis())]

    worker = rq.Worker(queues)
    worker.push_exc_handler(error_handler)
    worker.work()
