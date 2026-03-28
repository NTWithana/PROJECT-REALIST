# Build stage
FROM node:20-alpine AS build
WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine AS final
WORKDIR /app

# Install only production dependencies
COPY package*.json ./
RUN npm install --omit=dev

# Copy build output
COPY --from=build /app/.next ./.next
COPY --from=build /app/public ./public

# Copy config files
COPY --from=build /app/next.config.js ./
COPY --from=build /app/package*.json ./

EXPOSE 3000
CMD ["npm", "start"]