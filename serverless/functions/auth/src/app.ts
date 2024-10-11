import * as dotenv from 'dotenv';
dotenv.config();
import { Database, Events } from './helpers/database';

import cookieParser from 'cookie-parser';
import express, { Express } from 'express';
import cors from 'cors';

import * as auth from './routes/auth';

let db: Database;
let app: Express;

app = express();

console.log('startExpressServer Function---------------->');
// if in dev environment allow cross domain requests.
if (process.env.DEV === 'true') app.use(cors());

app.use(cookieParser());
app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// export let handler: serverless.Handler;
// function which connects database. If error, it retrys. If successful, updates all of the routes with the new database object, then starts the express server.
const connectToDatabase = async (
  req: express.Request,
  res: express.Response,
  next: (err?: any) => void
) => {
  db = new Database();
  db.on(Events.ERROR, (err) => {
    console.log('database connection error -------------->', err);
    res.status(503).json([
      {
        message: err,
      },
    ]);
  });

  db.on(Events.CONNECTED, () => {
    console.log('database connection success------------------>');
    auth.setDatabase(db);
    next();
  });
};

app.use(connectToDatabase);

app.use('/', auth.default);

export default app;
