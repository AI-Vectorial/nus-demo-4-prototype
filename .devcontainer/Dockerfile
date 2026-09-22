FROM mcr.microsoft.com/devcontainers/python:3.12

# --- Node, for the Next.js frontend ------------------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# --- AI coding assistants ----------------------------------------------
# All three are installed. Which one a table uses is decided the week before
# delivery, not baked into the image. Swapping tools changes this block only.
RUN npm install -g \
      @anthropic-ai/claude-code \
      @openai/codex
# GitHub Copilot arrives as a VS Code extension, see devcontainer.json

# --- backend dependencies, baked in so start-up fetches nothing ---------
COPY backend/requirements-dev.txt /tmp/requirements-dev.txt
COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements-dev.txt

# --- the same quality gates CI runs, available locally ------------------
RUN pip install --no-cache-dir bandit pip-licenses pytest ruff
