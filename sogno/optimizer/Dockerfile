FROM python:3.9

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD routing_milp.py /
ADD SmartRouting.py /


CMD ["python", "-u","./SmartRouting.py"]