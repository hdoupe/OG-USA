FROM continuumio/miniconda3

USER root
RUN  apt-get update && apt install libgl1-mesa-glx vim --yes

RUN mkdir /home/OG-USA
RUN mkdir /home/outputs
RUN mkdir /home/outputs/OUTPUT_BASELINE
RUN mkdir /home/outputs/OUTPUT_REFORM

COPY ./conda-requirements.txt /home/OG-USA
WORKDIR /home/OG-USA
RUN conda install -c anaconda -c pslmodels --file conda-requirements.txt --yes

COPY ./ /home/OG-USA
RUN pip install -e .

WORKDIR /home/OG-USA/run_examples

ENTRYPOINT ["python", "run_ogusa_example.py"]