FROM python:3.8.5-slim
LABEL maintainer "ping@obradovic.com"
WORKDIR /usr/local/src

#
# PACKAGES
#
RUN apt update && apt install -y \
    curl \
    vim \
    unzip \
    xvfb

#
# CHROMEDRIVER (CHROME)
#
RUN export VERSION=86.0.4240.22 && export ZIP=chromedriver_linux64.zip && \
    curl -O https://chromedriver.storage.googleapis.com/$VERSION/$ZIP && \
    unzip $ZIP && \
    rm $ZIP && \
    mv chromedriver /usr/local/bin/.

#
# GECKODRIVER (FIREFOX)
#
RUN export VERSION=0.27.0 && export TGZ="geckodriver-v$VERSION-linux64.tar.gz" && \
    curl -L -O https://github.com/mozilla/geckodriver/releases/download/v$VERSION/$TGZ && \
    tar zxfv $TGZ && \
    rm $TGZ && \
    mv geckodriver /usr/local/bin/.

#
# PYTHON
#
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY google-domains.yaml /etc/.
COPY dist/*.whl .
RUN pip install *.whl

# CMD "/bin/bash"
ENTRYPOINT ["/bin/bash"]
