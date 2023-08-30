FROM python:3.11.5-alpine
RUN pip install -r requirements.txt
COPY . /app
WORKDIR /app
CMD ["python", "main.py"]
