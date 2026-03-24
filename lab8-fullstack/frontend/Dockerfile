FROM node:20-alpine

# Used when next.config rewrites() runs during `next build` / `next start`
ARG BACKEND_INTERNAL_URL=http://backend:8000
ENV BACKEND_INTERNAL_URL=$BACKEND_INTERNAL_URL

WORKDIR /srv/frontend

COPY package.json ./
RUN npm install

COPY . ./
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start", "--", "-H", "0.0.0.0", "-p", "3000"]
