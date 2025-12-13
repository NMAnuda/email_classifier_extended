# Use debian-based Node (glibc for LightningCSS—avoids alpine musl issues)
FROM node:20

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --include=dev  # Include dev for Tailwind/LightningCSS during build

# Copy code
COPY . .

# Build for prod (Tailwind processes globals.css)
RUN npm run build

EXPOSE 3000

# Start prod (omits devDeps)
CMD ["npm", "start"]