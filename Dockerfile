FROM conda/miniconda3

RUN conda install yacron git python=3.8 gmp pandoc tectonic -c conda-forge
RUN pip install git+https://github.com/apoorvkh/obsidian-remarkable-sync.git@remarks
RUN pip install git+https://github.com/apoorvkh/obsidian-remarkable-sync.git@obs2rem

RUN echo 'jobs:\n  - name: sync\n    command: python -m obs2rem --obsidian-dir /obsidian --remarkable-dir /remarkable && python -m remarks /remarkable /obsidian/remarkable\n    shell: /bin/bash\n    schedule: "*/5 * * * *"' > /crontab.yml

ENTRYPOINT "yacron -c /crontab.yml"
