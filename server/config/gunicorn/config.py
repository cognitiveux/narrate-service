import multiprocessing

bind = '0.0.0.0:10000'
backlog = 2048
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'gevent'
worker_connections = 1000
timeout = 500
keepalive = 120
