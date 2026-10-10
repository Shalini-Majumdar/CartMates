# Vite 7 requires Node ^20.19 || >=22.12
FROM node:22

WORKDIR /app

COPY package*.json ./

RUN npm install

COPY . .

EXPOSE 3000

# vite.config.js sets host: true so the server is reachable from outside
# the container.
CMD ["npm", "run", "dev"]
