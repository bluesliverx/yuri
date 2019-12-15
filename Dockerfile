FROM python:3.7-alpine
RUN apk --no-cache add gcc musl-dev g++
RUN pip install -U pip Cython
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
RUN mkdir -p /app/oncall_slackbot /app/slacker_blocks
ENV PYTHONPATH=/app
ADD oncall_slackbot /app/oncall_slackbot
ADD slacker_blocks /app/slacker_blocks
