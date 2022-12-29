FROM python
RUN pip install requests
RUN pip install --pre "python-telegram-bot==20.0b0"
COPY main.py main.py
CMD ["python3", "/main.py"]
