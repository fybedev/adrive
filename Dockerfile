FROM python:3.9.5
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN mkdir -p /app/uploads
RUN mkdir -p lightdb/databases
RUN touch lightdb/databases/db.sqlite
EXPOSE 3133

CMD ["python", "app.py"]