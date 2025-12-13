FROM node:20-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy code
COPY . .

# Build for prod
RUN npm run build

EXPOSE 3000

# Start (no secrets exposed)
CMD ["npm", "start"]