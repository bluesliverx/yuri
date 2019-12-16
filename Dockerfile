FROM bksaville/oncall-slackbot-base:latest
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
ENV PYTHONPATH=/app
RUN mkdir -p /app/yuri
ADD yuri /app/yuri/
ADD bin/yuri /
ENTRYPOINT ["/yuri"]
