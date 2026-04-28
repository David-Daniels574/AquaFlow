# Stage 1: Build the React application
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Stage 2: Serve the application with NGINX
FROM nginx:alpine
# Copy the build output from Stage 1 to NGINX html folder
COPY --from=build /app/dist /usr/share/nginx/html
# Copy a custom NGINX config if you have one, or use default
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]