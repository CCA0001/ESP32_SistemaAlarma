FROM python:3.12-slim
WORKDIR /app
RUN pip install flask paho-mqtt mysql-connector-python
COPY app.py .
CMD ["python", "app.py"]
