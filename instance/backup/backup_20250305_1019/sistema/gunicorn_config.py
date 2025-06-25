bind = "0.0.0.0:8000"
workers = 3
timeout = 120
keepalive = 5
errorlog = "logs/gunicorn-error.log"
accesslog = "logs/gunicorn-access.log"
capture_output = True
