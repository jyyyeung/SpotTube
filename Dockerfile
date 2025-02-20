FROM docker.io/oz123/pipenv:3.12-v2024-12-16 AS builder


# Tell pipenv to create venv in the current directory
ENV PIPENV_VENV_IN_PROJECT=1

# Pipfile contains requests
ADD Pipfile.lock Pipfile /usr/src/

WORKDIR /usr/src

# NOTE: If you install binary packages required for a python module, you need
# to install them again in the runtime. For example, if you need to install pycurl
# you need to have pycurl build dependencies libcurl4-gnutls-dev and libcurl3-gnutls
# In the runtime container you need only libcurl3-gnutls

# RUN apt install -y libcurl3-gnutls libcurl4-gnutls-dev

RUN /root/.local/bin/pipenv sync

RUN /usr/src/.venv/bin/python -c "import requests; print(requests.__version__)"

FROM python:3.12-alpine

# Set build arguments
ARG RELEASE_VERSION
ENV RELEASE_VERSION=${RELEASE_VERSION}

# Install ffmpeg
RUN apk update && apk add --no-cache ffmpeg su-exec

# Create directories and set permissions
COPY . /spottube
WORKDIR /spottube

# Install requirements
RUN mkdir -v /spottube/.venv
COPY --from=builder /usr/src/.venv/ /spottube/.venv/

# Make the script executable
RUN chmod +x thewicklowwolf-init.sh

# Expose port
EXPOSE 5000

# Start the app
ENTRYPOINT ["./thewicklowwolf-init.sh"]
