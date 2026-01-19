FROM mitmproxy/mitmproxy:10.2.4

COPY proxy.py /app/proxy.py

CMD ["mitmdump", "-s", "/app/proxy.py", "--mode", "reverse:http://node-api:3000"]
