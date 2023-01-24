FROM python:3.9

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD pricing_rule.py /
ADD api.py /

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "9003","--reload"]