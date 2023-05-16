FROM python
RUN pip install requests python-telegram-bot
COPY main.py main.py
CMD ["python3", "/main.py"]
