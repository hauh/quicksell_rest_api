FROM python:slim
ENV \
	PYTHONBUFFERED=1 \
	PYTHONDONTWRITEBYTECODE=1
RUN \
	apt-get update && apt-get upgrade -y && \
	apt-get install -y libpq-dev gcc && \
	apt-get clean
WORKDIR /opt/app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY quicksell ./quicksell
