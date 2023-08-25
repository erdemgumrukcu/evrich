FROM python:3.9

RUN apt-get update && \
    apt-get install -y glpk-utils

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD routing_milp.py /
ADD SmartRouting.py /

CMD ["python", "-u","./SmartRouting.py"]