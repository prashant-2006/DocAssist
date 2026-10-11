# my-app/Dockerfile
FROM node:20-alpine

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm install

# Copy the frontend code
COPY . .

EXPOSE 3000

# Run in development mode
CMD ["npm", "run", "dev"]