ARG VLLM_VERSION=v0.7.3
FROM vllm/vllm-openai:${VLLM_VERSION}

# Copy the new entrypoint script
COPY sagemaker/serve /usr/bin/serve

# Ensure the serve script has executable permissions
RUN chmod +x /usr/bin/serve

# Expose port 8080
EXPOSE 8080

# Set the serve script as the entrypoint
ENTRYPOINT ["/usr/bin/serve"]
