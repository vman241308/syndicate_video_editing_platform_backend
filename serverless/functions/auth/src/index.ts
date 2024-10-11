import { APIGatewayEvent } from 'aws-lambda';
import serverless from 'serverless-http';
import app from './app';
import http from 'http';

const { PORT = 8080 } = process.env;

// create handler
const createHandler = (app: any, basePath: string) => {
  return async (event: APIGatewayEvent, context: any) => {
    console.info(`${event.httpMethod} - ${event.path}`);
    console.info('Bootstraping server with serverless-http');
    const server = bootstrapServer(app, basePath);
    const result = await server(event, context);
    console.log('Result ----------> ', result);
    return result;
  };
};

// create bootstrapserver

const bootstrapServer = (app: any, path: string) => {
  return serverless(app, {
    request(request: any, event: APIGatewayEvent, context: any) {
      request.apiGateway = { event, context };
    },
    basePath: path,
  });
};

let server;

if (process.env.DEV) {
  server = http.createServer(app).listen(PORT, () => {
    console.log(`Express app running at ${PORT}  Port`);
  });
} else {
  server = createHandler(app, '');
}

export const handler = server;
