# Dashboard image (multi-stage).
# Purpose: Build the Vite SIEM dashboard and serve the static bundle via nginx.
# Security: VITE_* values are build args (not secrets); nginx serves read-only
# static assets. Authenticate users at a reverse proxy in front of this.
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json ./
RUN npm install
COPY . .
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
