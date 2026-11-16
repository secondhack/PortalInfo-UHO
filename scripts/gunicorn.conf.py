# Linux: instalar gunicorn y usar desde backend: gunicorn -c ../scripts/gunicorn.conf.py config.wsgi
bind = '127.0.0.1:8010'
workers = 2
threads = 4
worker_class = 'gthread'
backlog = 256
forwarded_allow_ips = '127.0.0.1'
timeout = 30
accesslog = '-'
errorlog = '-'
