FROM docker.io/library/node:20-alpine AS builder

ARG PUBLIC_API_BASE_URL=/api

WORKDIR /app

COPY package.json ./
RUN npm install

COPY . .

RUN sh -c 'echo "Building with PUBLIC_API_BASE_URL=$PUBLIC_API_BASE_URL" && PUBLIC_API_BASE_URL=$PUBLIC_API_BASE_URL npm run build'

FROM node:20-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/build /app/build

EXPOSE 3000

CMD ["serve", "-s", "/app/build", "-l", "3000"]
