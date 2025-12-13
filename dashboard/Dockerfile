# Use debian-based Node (bookworm/glibc for LightningCSS compat—no alpine musl issues)
FROM node:20-bookworm-slim

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --include=dev  # Include dev for Tailwind/LightningCSS during build

# Install LightningCSS explicitly (fixes binary mismatch)
RUN npm install lightningcss@1.25.1 --save-dev

# Copy code
COPY . .

# Build for prod (Tailwind processes globals.css)
RUN npm run build

EXPOSE 3000

# Start prod (omits devDeps)
CMD ["npm", "start"]