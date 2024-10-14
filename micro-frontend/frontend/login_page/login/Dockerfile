# micro-frontend/frontend/login_page/Dockerfile

# Stage 1: Build the React app
FROM node:16-alpine as build

# Set working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . ./

# Build the React app
RUN npm run build

# Stage 2: Prepare build artifacts for Nginx
FROM alpine:latest

# Install necessary tools
RUN apk add --no-cache bash

# Create directory for build artifacts
RUN mkdir -p /build/login_page

# Copy build files from previous stage
COPY --from=build /app/build /build/login_page

# Default command
CMD ["echo", "Build completed for login_page"]
