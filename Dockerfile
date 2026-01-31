FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN addgroup -S app && adduser -S app -G app
USER app

EXPOSE 8080



CMD ["npm", "start"]