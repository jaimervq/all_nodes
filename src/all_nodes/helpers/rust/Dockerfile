# Start with Python 3.10 base image
FROM python:3.10

# Install Rust
RUN apt-get update && apt-get install -y curl build-essential && \
    curl https://sh.rustup.rs -sSf | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

# Set working directory
WORKDIR /usr/src

# Copy Rust source files
COPY ./rust_noise ./rust_noise
COPY ./rust_regex ./rust_regex

# Copy your bash script for build/rename
COPY ./build_and_rename_libs.sh /usr/local/bin/build_and_rename_libs.sh
RUN chmod +x /usr/local/bin/build_and_rename_libs.sh

# Bash script as the container entrypoint
CMD ["/usr/local/bin/build_and_rename_libs.sh"]