FROM python
RUN pip install requests python-telegram-bot
COPY main.py main.py
ENTRYPOINT ["python3", "/main.py"]
