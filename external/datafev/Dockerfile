FROM python:3.9

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

# Copy your application code and data
COPY data_handling/ /app/data_handling/
COPY api.py /app/
COPY outputs/ /app/outputs/

# Command to run your FastAPI application without auto-reloading
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "9004","--reload"]
