FROM python:slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
RUN apt-get update && apt-get upgrade -y && \
	apt-get install -y \
		libpq-dev gcc mailutils postfix \
		binutils libproj-dev gdal-bin && \
	apt-get clean && \
	postconf mydestination=localhost inet_interfaces=loopback-only
WORKDIR /opt/app
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
	pip install setuptools wheel && \
	pip install -r requirements.txt
COPY quicksell .
COPY entrypoint.sh .
ENTRYPOINT ["./entrypoint.sh"]
