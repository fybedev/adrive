FROM python:3.9.5
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
COPY container/* .
RUN mkdir -p /app/uploads
EXPOSE 3133

CMD ["python", "app.py"]