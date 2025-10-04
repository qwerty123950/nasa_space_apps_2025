FROM node:18-alpine as build
WORKDIR /app
COPY ../frontend /app
RUN npm i -g pnpm && pnpm i && pnpm build
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx","-g","daemon off;"]