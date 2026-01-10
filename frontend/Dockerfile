# EAZY Frontend Dockerfile
# Multi-stage build with Node.js and Nginx

# =============================================================================
# Stage 1: Builder - Build the React application
# =============================================================================
FROM node:22-alpine as builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# =============================================================================
# Stage 2: Runtime - Serve with Nginx
# =============================================================================
FROM nginx:alpine as runtime

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose HTTP port
EXPOSE 80

# Run nginx in foreground
CMD ["nginx", "-g", "daemon off;"]
