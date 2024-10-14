# Stage 1: Build the React app
FROM node:16-alpine AS build

# Set working directory
WORKDIR /LuminacerisBank/microfrontend/history_page

# Copy package.json and package-lock.json
COPY package.json package-lock.json ./

# Install dependencies
RUN npm install

# Copy the rest of the source code
COPY . ./

# Build the React app
RUN npm run build

# Stage 2: Deploy to Nginx
FROM nginx:stable-alpine

# Remove default Nginx static files
RUN rm -rf /usr/share/nginx/html/*

# Copy build artifacts from the build stage
COPY --from=build /LuminacerisBank/microfrontend/history_page/build /usr/share/nginx/html/history_page

# Expose port 80
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
