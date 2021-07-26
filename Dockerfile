FROM python:3.7
ADD requirements.txt .
RUN python3 -m pip install -r requirements.txt
ADD ./main.py .
ADD ./api_key.txt .
ENTRYPOINT ["./main.py"]
