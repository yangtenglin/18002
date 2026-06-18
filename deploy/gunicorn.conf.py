import multiprocessing
import os

bind = '127.0.0.1:8000'
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 120
keepalive = 5

backlog = 2048

errorlog = os.path.expanduser('~/hotel-simulation/logs/gunicorn.error.log')
accesslog = os.path.expanduser('~/hotel-simulation/logs/gunicorn.access.log')
loglevel = 'info'

proc_name = 'hotel-simulation'

user = None
group = None

raw_env = [
    'DJANGO_SETTINGS_MODULE=backend.settings_prod',
]

preload_app = True
max_requests = 1000
max_requests_jitter = 50
