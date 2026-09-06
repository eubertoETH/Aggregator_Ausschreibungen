FROM alpine:3.22

WORKDIR /app
COPY Code/ /app/
EXPOSE 8080
CMD ["sh", "-c", "while true; do printf 'service-template running\\n'; sleep 3600; done"]
