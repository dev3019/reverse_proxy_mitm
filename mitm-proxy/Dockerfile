FROM mitmproxy/mitmproxy:10.2.4

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app/.

CMD ["mitmdump", "-s", "/app/proxy.py"]

