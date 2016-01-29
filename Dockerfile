FROM continuumio/anaconda3
RUN useradd -ms /bin/bash pystarlab
RUN conda install -y django

# build environment for starlab
RUN apt-get update --quiet && apt-get install --yes \
       --no-install-recommends --no-install-suggests \
       build-essential \
       module-init-tools \
       wget \
       libboost-all-dev \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

ENV STARLAB_DOWNLOAD https://www.dropbox.com/s/tzwimr7e9hrmpm1/starlabDockerPublic.tar.gz
RUN wget --no-check-certificate $STARLAB_DOWNLOAD
RUN tar xvzf starlabDockerPublic.tar.gz
RUN cd starlab && ./configure --with-f77=no --with-grape=no --prefix=/usr/local \
    && make && make install && cd ..

WORKDIR /home/pystarlab
ADD notebooks /home/pystarlab/notebooks
ADD pystarlab /home/pystarlab/pystarlab
RUN chown -R pystarlab /home/pystarlab
WORKDIR /home/pystarlab/notebooks
EXPOSE 8888
ENTRYPOINT ["tini", "--"]
ENV HOME /home/pystarlab

USER pystarlab
CMD ["jupyter", "notebook", "--no-browser", "--ip=*"]
