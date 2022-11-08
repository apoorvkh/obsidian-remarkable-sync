FROM conda/miniconda3

RUN conda install yacron git python=3.8 gmp pandoc tectonic -c conda-forge
RUN pip install git+https://github.com/apoorvkh/obsidian-remarkable-sync.git@remarks
RUN pip install git+https://github.com/apoorvkh/obsidian-remarkable-sync.git@obs2rem

COPY ./crontab.yml /crontab.yml

ENTRYPOINT ["/usr/local/bin/yacron", "-c", "/crontab.yml"]
