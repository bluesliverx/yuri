FROM python:3.7-alpine
RUN apk --no-cache add gcc musl-dev g++
RUN pip install -U pip Cython
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
RUN mkdir -p /app
ENV PYTHONPATH=/app
ADD oncall_slackbot /app/
ADD slacker_blocks /app/
