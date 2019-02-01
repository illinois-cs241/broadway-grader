FROM alpine:3.8

RUN apk add python3 git

COPY src /grader

RUN pip3 install -r /grader/requirements.txt

RUN echo "#! /bin/sh" >> /grader/run.sh && \
    echo "cd /grader && python3 run.py \"\$@\"" >> /grader/run.sh && \
    chmod +x /grader/run.sh && \
    ln -s /grader/run.sh /usr/bin/grader

CMD [ "/bin/sh" ]
