FROM node:20-alpine as builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install --silent
COPY . .
RUN npm run build

FROM nginx:stable-alpine
# Add a simple nginx config to serve SPA (fallback to index.html)
COPY --from=builder /app/dist /usr/share/nginx/html
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/spa.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
