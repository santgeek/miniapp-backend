FROM python:3.10-slim-buster as python_builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    graphviz \
    libgraphviz-dev \
    gcc \
    default-libmysqlclient-dev \
    pkg-config

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

FROM node:16 as final_stage

RUN apt update \
    && apt install -y --no-install-recommends graphviz 
    

WORKDIR /opt/app

COPY --from=python_builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=python_builder /usr/local/bin/ /usr/local/bin/

COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh 

RUN echo "--- Contents of /usr/local/bin/ during build stage ---" && \
    ls -la /usr/local/bin/ && \
    echo "-----------------------------------------------"

RUN test -f /usr/local/bin/start.sh || (echo "BUILD ERROR: start.sh file NOT found in /usr/local/bin/ after COPY!" && exit 1)
RUN test -x /usr/local/bin/start.sh || (echo "BUILD ERROR: start.sh not executable in /usr/local/bin/!" && exit 1)
# -----------------------------------------------------------------

COPY . /opt/app/src 

ENV PATH="/usr/local/bin:$PATH"
ENV NODE_ENV=container
ENV FLASK_APP=src/app.py
ENV BASENAME=/
ENV DEBUG=TRUE 

CMD ["/usr/local/bin/start.sh"]