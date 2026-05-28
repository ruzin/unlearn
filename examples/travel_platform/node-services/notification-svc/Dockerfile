FROM node:20-slim
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY src ./src
EXPOSE 8081
CMD ["node", "--loader", "ts-node/esm", "src/index.ts"]
