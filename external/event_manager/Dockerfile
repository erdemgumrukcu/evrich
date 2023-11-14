FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy your application code and data
COPY data_handling/ /app/data_handling/
COPY event_manager.py /app/

CMD ["python", "-u","./event_manager.py"]
