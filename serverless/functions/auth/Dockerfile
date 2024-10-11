FROM public.ecr.aws/lambda/nodejs:18.2023.04.04.11 as builder
RUN mkdir -p /app
COPY functions/auth/package.json /app/package.json
COPY functions/auth/tsconfig.json /app/tsconfig.json
COPY functions/auth/nodemon.json /app/nodemon.json
WORKDIR /app
RUN npm install
COPY functions/auth/. /app/
RUN npm run build


FROM public.ecr.aws/lambda/nodejs:18.2023.04.04.11
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder /app/build/ ./
COPY --from=builder  /app/package* ./
RUN npm install --omit=dev
EXPOSE ${PORT}
ENV PORT=${PORT}
# ENTRYPOINT ["node", "index.js"]
CMD ["index.handler"]
