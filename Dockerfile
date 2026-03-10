# Stage 1: Build the frontend
FROM node:20-slim AS build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Production environment
FROM node:20-slim
WORKDIR /app

# Install production dependencies only
COPY package*.json ./
RUN npm install --production

# Copy built assets from build-stage
COPY --from=build-stage /app/dist ./dist
# Copy server code
COPY server.ts ./
# Copy other necessary files
COPY metadata.json ./
COPY .env.example ./.env

# Install tsx to run the server
RUN npm install -g tsx

EXPOSE 3000

# Start the application
CMD ["tsx", "server.ts"]
