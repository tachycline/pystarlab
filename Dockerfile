FROM continuumio/anaconda3
RUN useradd -ms /bin/bash pystarlab
WORKDIR /usr/local
RUN curl -SL http://atlacamani.marietta.edu:/depot/starlab-binaries.tar.bz2 | tar xjf -
USER pystarlab
WORKDIR /home/pystarlab
RUN git clone https://github.com/tachycline/pystarlab
WORKDIR /home/pystarlab/pystarlab/notebooks
EXPOSE 8888
ENV HOME /home/pystarlab
CMD ["jupyter", "notebook", "--no-browser", "--ip=*"]
