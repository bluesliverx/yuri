FROM jgontrum/spacyapi:en_v2
COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
ADD bin/yuri /
ENTRYPOINT ["/yuri"]
