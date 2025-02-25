FROM python:3.12-alpine

RUN mkdir -p /app
WORKDIR /app

COPY Pipfile* .

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install & use pipenv
RUN python -m pip install pipenv

# Install ffmpeg
RUN apk update && \
  apk add --no-cache \
  build-base cmake ffmpeg su-exec

RUN pipenv sync --system

COPY . .

RUN python -c "import requests; print(requests.__version__)"

# Set build arguments
ARG RELEASE_VERSION
ENV RELEASE_VERSION=${RELEASE_VERSION}

# Make the script executable
RUN chmod +x thewicklowwolf-init.sh

# Expose port
EXPOSE 5050

# Start the app
ENTRYPOINT ["./thewicklowwolf-init.sh"]
