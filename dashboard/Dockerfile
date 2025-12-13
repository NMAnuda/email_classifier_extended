# Use debian-based Node (glibc for LightningCSS compatibility—no alpine musl issues)
FROM node:20

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --include=dev  # Fixed: Include devDeps for Tailwind build (LightningCSS needs it)

# Copy code
COPY . .

# Build for prod (Tailwind processes)
RUN npm run build

EXPOSE 3000

# Start (prod mode skips devDeps)
CMD ["npm", "start"]