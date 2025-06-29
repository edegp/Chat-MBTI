# Flutter Web Development Container
FROM ghcr.io/cirruslabs/flutter:stable

# Set working directory
WORKDIR /app

# Install additional dependencies for web development
RUN apt-get update && apt-get install -y \
    curl \
    git \
    unzip \
    xz-utils \
    zip \
    libglu1-mesa \
    chromium-browser \
    && rm -rf /var/lib/apt/lists/*

# Configure Flutter for web development
RUN flutter config --enable-web
RUN flutter doctor

# Copy pubspec files first for better caching
COPY pubspec.yaml pubspec.lock ./

# Get dependencies
RUN flutter pub get

# Copy the rest of the application
COPY . .

# Expose port 3000 for Flutter web server
EXPOSE 3000

# Command to run Flutter web in development mode with hot reload
CMD ["flutter", "run", "-d", "web-server", "--web-port=3000", "--web-hostname=0.0.0.0", "--hot", "--debug"]
