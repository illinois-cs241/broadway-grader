FROM alpine:3.8

RUN apk add python3 git

COPY src /grader

RUN pip3 install -r /grader/requirements.txt

ENTRYPOINT [ "python3", "/grader/run.py" ]
