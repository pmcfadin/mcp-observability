FROM alpine:3.20

RUN apk add --no-cache openssl

# Copy entrypoint
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

VOLUME ["/certs"]

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"] 