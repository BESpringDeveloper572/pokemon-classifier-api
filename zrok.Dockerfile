FROM openziti/zrok2:latest

# Ensure we are explicitly using the built-in non-root user
USER ziggy

# Create the folder within ziggy's owned home space
RUN mkdir -p /home/ziggy/.zrok2

# Optional: Set the working directory to home
WORKDIR /home/ziggy