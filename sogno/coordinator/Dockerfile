FROM python:3.9

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD controller.py /

CMD ["python", "-u","./controller.py"]