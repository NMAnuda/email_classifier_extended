# Use Node 20 alpine for small size
FROM node:20-alpine

# Set work dir
WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy code
COPY . .

# Build for prod
RUN npm run build

# Expose port
EXPOSE 3000

# Start with node (optimized)
CMD ["npm", "start"]