# Two stages. One to build the neuron modules and one to run them. Assumption
# is that you can play around with parameters in the second stage and
# re-run the octave code without having to rebuild the whole thing.

# FIRST STAGE
FROM debian:sid AS builder
COPY SchreglmannEtAl2020 /opt/SchreglmannEtAl2020
RUN apt-get update && \
    apt-get install \
    neuron \
    neuron-dev \
    openmpi-bin \
    libmeschach-dev \
    libopenmpi-dev \
    libreadline-dev \
    libncurses-dev

WORKDIR /opt/SchreglmannEtAl2020/CCTC_model/modfiles
RUN nrnivmodl
RUN mv x86_64 ../

# SECOND STAGE
FROM debian:sid 
COPY --from=builder /opt/SchreglmannEtAl2020 /opt/
WORKDIR /opt/SchreglmannEtAl2020/CCTC_model
RUN apt-get update && \
    apt-get install \
    octave \
    python3-neuron \
    octave-signal

ENTRYPOINT octave 
