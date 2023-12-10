FROM python:3.11

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

WORKDIR /app

RUN mkdir /app/static
RUN mkdir /app/media

RUN apt-get update && rm -rf /var/lib/apt/lists/*

COPY requirements.txt requirements.txt

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install 'transformers[torch]'


COPY stock_analysis .

CMD ["gunicorn", "stock_analysis.wsgi:application", "--bind", "0.0.0.0:8000"]