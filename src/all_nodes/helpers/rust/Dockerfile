FROM python:3.10

# Install Rust
RUN apt-get update && apt-get install -y curl build-essential && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

WORKDIR /usr/src

# Copy entire folder
COPY . .

# Normalize script + make executable
RUN apt-get update && apt-get install -y dos2unix
RUN dos2unix /usr/src/build_and_rename_libs.sh
RUN chmod +x /usr/src/build_and_rename_libs.sh || true

CMD ["/usr/src/build_and_rename_libs.sh"]
#ENTRYPOINT ["tail", "-f", "/dev/null"]
