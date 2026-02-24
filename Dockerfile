FROM python:3.14-slim

RUN adduser --uid 1234 nando

RUN python -m venv /.venv
ENV PATH="/.venv/bin:$PATH"

ENV TZ=America/Argentina/Buenos_Aires

RUN pip install --upgrade pip

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt

COPY src /src

WORKDIR /src

RUN python manage.py collectstatic --noinput

ENV DJANGO_DEBUG_FALSE=1

USER nando

CMD ["gunicorn", "--bind", ":8004", "finper.wsgi:application"]
