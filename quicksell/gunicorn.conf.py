"""Gunicorn configuration file."""

import multiprocessing

bind = '0.0.0.0:8000'
backlog = 2048
worker_class = 'gthread'
workers = multiprocessing.cpu_count() * 2 + 1
worker_connections = 1000
timeout = 30
keepalive = 3
