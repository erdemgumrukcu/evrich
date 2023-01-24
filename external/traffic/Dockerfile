FROM python:3.9

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD api.py /

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000","--reload"]