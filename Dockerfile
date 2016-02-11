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

# clean up after starlab install
RUN rm -rf starlab starlabDockerPublic.tar.gz sapporo

WORKDIR /home/pystarlab
VOLUME /home/pystarlab
EXPOSE 5000
EXPOSE 8888
ENTRYPOINT ["tini", "--"]
ENV HOME /home/pystarlab

USER pystarlab
CMD ["jupyter", "notebook", "--no-browser", "--ip=*"]
