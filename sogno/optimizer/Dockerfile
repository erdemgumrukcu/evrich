FROM python:3.9
FROM continuumio/anaconda3

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

RUN conda config --set channel_priority false
RUN conda update --all --yes
RUN conda install -c conda-forge/label/gcc7 glpk

ADD routing_milp.py /
ADD SmartRouting.py /


CMD ["python", "-u","./SmartRouting.py"]