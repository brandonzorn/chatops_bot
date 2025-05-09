FROM python:3.13-alpine

COPY ./requirements /requirements
RUN pip install --no-cache-dir -r requirements/prod.txt
RUN rm -rf requirements

COPY ./chatopsbot /chatopsbot/
WORKDIR /chatopsbot

CMD ["python", "main.py"]