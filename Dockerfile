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
COPY --from=python_builder /usr/local/lib/python3.10/ /usr/local/lib/python3.10/ 
COPY --from=python_builder /usr/local/lib/ /usr/local/lib/

COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh 

COPY . /opt/app 

ENV PATH="/usr/local/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/lib:$LD_LIBRARY_PATH"
ENV PYTHONPATH="/opt/app:$PYTHONPATH"
ENV NODE_ENV=container
ENV FLASK_APP=src.wsgi
ENV BASENAME=/
ENV DEBUG=TRUE 

CMD ["/usr/local/bin/start.sh"]