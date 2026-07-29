FROM python:3.14
RUN pip install requests python-telegram-bot
COPY main.py main.py
ENTRYPOINT ["python3", "/main.py"]
