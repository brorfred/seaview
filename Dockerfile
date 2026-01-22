FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including fontconfig
RUN apt-get update && \
    apt-get install -y curl fontconfig rsync && \
    rm -rf /var/lib/apt/lists/*

# Install pixi
RUN curl -fsSL https://pixi.sh/install.sh | bash && \
    echo 'export PATH="/root/.pixi/bin:$PATH"' >> /root/.bashrc

# Install pipx
RUN pip install --no-cache-dir pipx

# Ensure binaries are in PATH
ENV PATH="/root/.local/bin:$PATH"
ENV PATH="/root/.pixi/bin:$PATH"

# Copy everything
COPY . .

# Install dependencies
RUN pixi install
RUN pipx install .
