FROM python:3.8.5-slim
LABEL maintainer "ping@obradovic.com"

#
# ENV
#
WORKDIR /usr/local/src
ENV DISPLAY=:0


#
# PACKAGES
#
RUN apt update && apt install -y \
    curl \
    gnupg2 \
    procps \
    supervisor \
    unzip \
    vim \
    xvfb \
    firefox-esr


#
# INSTALL GECKODRIVER / FIREFOX
#
RUN export VERSION=0.26.0 && \
    export TGZ="geckodriver-v$VERSION-linux64.tar.gz" && \
    curl -L -O https://github.com/mozilla/geckodriver/releases/download/v$VERSION/$TGZ && \
    tar zxfv $TGZ && \
    rm $TGZ && \
    mv geckodriver /usr/local/bin/.


#
# INSTALL CHROMEDRIVER / CHROME
#
RUN export VERSION=85.0.4183.87 && \
    export ZIP=chromedriver_linux64.zip && \
    curl -O https://chromedriver.storage.googleapis.com/$VERSION/$ZIP && \
    unzip $ZIP && \
    rm $ZIP && \
    mv chromedriver /usr/local/bin/.

RUN echo "deb http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list && \
    curl https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    apt update && \
    apt install -y \
        google-chrome-stable \
        chromium
        # chromium-l10n

# RUN export CHROME_VERSION=85.0.4183.10 && \
    # export CHROME_DEB="google-chrome-stable_$CHROME_VERSION_amd64.deb" && \
    # curl -O https://dl.google.com/linux/direct/$CHROME_DEB && \
    # apt install -y $CHROME_DEB && \
    # rm $CHROME_DEB

#
# PYTHON
#
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY google-domains.yaml /etc/.
COPY dist/*.whl .
RUN pip install *.whl

COPY supervisor-xvfb.conf /etc/supervisor/conf.d
CMD ["supervisord", "-n"]
# ENTRYPOINT ["supervisord", "-n"]
