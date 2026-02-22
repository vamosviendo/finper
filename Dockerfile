FROM python:3.14-slim

RUN python -m venv /.venv
ENV PATH="/.venv/bin:$PATH"

ENV TZ=America/Argentina/Buenos_Aires

RUN pip install --upgrade pip
RUN pip install "django<7" "django-case-insensitive-field==1.0.7"

COPY src /src

WORKDIR /src

CMD ["python", "manage.py", "runserver", "0.0.0.0:8004"]
