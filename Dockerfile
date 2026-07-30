FROM python:3.14-alpine

RUN adduser -D user
USER user

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install --user --no-cache-dir \
    python-telegram-bot \
    requests

COPY --chown=user:user \
    README.md \
    LICENSE \
    main.py \
    /src/
ENTRYPOINT ["python3", "/src/main.py"]
