FROM python:3.9

# Environment variables
ENV CLUSTER_ID=""
ENV IP_ADDRESS=""
ENV PORT_NUMBER=""

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

ADD pricing_rule.py /
ADD api.py /

#CMD ["uvicorn", "api:app", "--host", "${IP_ADDRESS}", "--port", "${PORT_NUMBER}", "--reload"]
CMD sh -c "uvicorn api:app --host $IP_ADDRESS --port $PORT_NUMBER --reload"
