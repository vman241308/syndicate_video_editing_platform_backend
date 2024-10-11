import express, { Request, Response } from 'express';
const router = express.Router();
import passwordValidator from 'password-validator';
import validator from 'validator';
import jwt, { JwtPayload } from 'jsonwebtoken';
import crypto from 'crypto';
import bcrypt from 'bcryptjs';
import { Database, Tables, Users } from '../helpers/database';
import BadParametersError, {
  BadParameters,
} from '../errors/BadParametersError';

// Generates random secret to be used for access token. This will reset upon a restart of the server, but mitigates potential security issues with storing it (this project also has only one instance needed).
const secret = crypto.randomBytes(256).toString('hex');
let database: Database;

// Password validation checker.
const schema = new passwordValidator();
schema
  .is()
  .min(8)
  .is()
  .max(100)
  .has()
  .uppercase(1, 'Password must have 1 uppercase letter')
  .has()
  .lowercase(1, 'Password must have 1 lowercase letter')
  .has()
  .digits(2, 'Password must have 2 digits')
  .has()
  .symbols(1, 'Password must have 1 symbol');

// any logged out tokens will be added to this blacklist to prevent relogging in using old tokens.
let loggedOutTokens: blacklist[] = [];

interface blacklist {
  token: string;
  expires: number;
}

router.get('/', async (req: Request, res: Response) => {
  res.json('This will be test');
});

// login route which expects password and email in body. Returns token
router.post('/login', async (req: Request, res: Response) => {
  console.log('Login user--------------->');
  try {
    if (!req.body.password || !req.body.email)
      throw new BadParametersError('Parameters not specified for body');
    const response = await database.searchForDataFromTable<Users>(
      Tables.USERS,
      'email',
      '=',
      req.body.email
    );
    let user = response[0];

    if (response.length === 0)
      throw new BadParametersError(
        'Invalid email or password',
        BadParameters.INVALID
      );

    const result = await bcrypt.compare(req.body.password, user.password);
    if (result !== true)
      throw new BadParametersError(
        'Invalid email or password',
        BadParameters.INVALID
      );
    else
      res.status(200).json({
        token: generateAccessToken(req.body.email),
      });
  } catch (error) {
    console.error(error);
    if (error instanceof BadParametersError) {
      if (error.getType() === BadParameters.DEFAULT) return res.status(400);

      return res.status(401).json([
        {
          validation: 'email or password',
          arguments: 0,
          message: 'Email or password is wrong',
        },
      ]);
    }

    res.status(500);
  }
});

// register route which expects password and email in body. Returns token
router.post('/register', async (req: Request, res: Response) => {
  console.log('Register user--------------->');
  try {
    if (!req.body.password || !req.body.email)
      throw new BadParametersError('Parameters not specified for body');
    if (!isValidEmail(req.body.email))
      throw new BadParametersError(
        'Must be a proper email',
        BadParameters.EMAIL
      );
    if (!isValidPassword(req.body.password))
      throw new BadParametersError('Invalid Password', BadParameters.PASSWORD);

    const response = await database.searchForDataFromTable<Users>(
      Tables.USERS,
      'email',
      '=',
      req.body.email
    );

    if (response.length !== 0)
      throw new BadParametersError('Email already exists', BadParameters.EMAIL);

    generateHash(req.body.password, async function (err, hash) {
      const responseStatus = await database.addRowIntoTable<Users>(
        Tables.USERS,
        {
          email: req.body.email,
          password: hash,
        }
      );

      if (responseStatus === false) throw new Error();

      const token = generateAccessToken(req.body.email);

      res.status(200).json({
        token,
      });
    });

    fetch('https://app.ayrshare.com/api/profiles/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.API_KEY}`,
      },
      body: JSON.stringify({
        title: 'ACME Profile', // required
      }),
    })
      .then((res) => res.json())
      .then((json) => console.log(json))
      .catch(console.error);
  } catch (error) {
    console.error(error);
    if (error instanceof BadParametersError) {
      if (error.getType() === BadParameters.DEFAULT) res.sendStatus(400);
      if (error.getType() === BadParameters.EMAIL)
        res.status(400).json([
          {
            validation: 'email',
            arguments: 0,
            message: error.message,
          },
        ]);
      if (error.getType() === BadParameters.PASSWORD)
        res.status(400).json(passwordDetails(req.body.password));
    } else res.sendStatus(500);
  }
});

export function passwordDetails(password: string) {
  return schema.validate(password, { details: true });
}

export function isValidPassword(password: string) {
  if (schema.validate(password)) return true;
  else false;
}

export function isValidEmail(email: string) {
  if (validator.isEmail(email)) return true;
  else false;
}

export function generateHash(
  text: string,
  callback: (error: Error, hash: string) => void
) {
  bcrypt.hash(text, 10, callback);
}

// creates access token which expires in 7 days
export function generateAccessToken(email: String) {
  try {
    return jwt.sign({ email }, secret, { expiresIn: 60 * 60 * 24 * 7 });
  } catch (error) {
    console.error(error);
  }
}

// route for checking if you are logged in.

router.get('/authed', authenticateToken, (req: Request, res: Response) => {
  console.log('Authed user--------------->');
  res.sendStatus(200);
});

// middleware for authenticating token, accepts authorization header or cookie for token. sends 401 if not authenticated
export function authenticateToken(req: Request, res: Response, next: Function) {
  const token = req.headers['authorization']
    ? req.headers['authorization']
    : req.cookies['authorization'];

  if (token == null) return res.sendStatus(401);
  if (checkBlacklist(token)) return res.sendStatus(403);

  jwt.verify(token, secret, (err: unknown, user: unknown) => {
    err = err as Error;
    user = user as { email: string };

    if (err) {
      console.log(err);
      return res.sendStatus(401);
    }

    req.user = user;

    next();
  });
}

router.patch(
  '/user',
  authenticateToken,
  async (req: Request, res: Response) => {
    try {
      let update: Partial<Users> = {};

      if (req.body.password !== undefined) update.password = req.body.password;

      if (req.body.instagram !== undefined)
        update.instagram = req.body.instagram;
      if (req.body.tiktok !== undefined) update.tiktok = req.body.tiktok;
      if (req.body.facebook !== undefined) update.facebook = req.body.facebook;
      if (req.body.youtube !== undefined) update.youtube = req.body.youtube;
      if (req.body.linkedin !== undefined) update.linkedin = req.body.linkedin;
      if (req.body.plan !== undefined) update.plan = req.body.plan;

      let response = await database.updateRowInTable<Users>(
        Tables.USERS,
        'email',
        '=',
        req.user.email,
        update
      );

      if (response === true) res.send(200);
      else res.send(400);
    } catch (error) {
      console.error(error);
      res.send(500);
    }
  }
);

// Verifies that token is legit, if so returns payload (email)
export function verifyToken(token: string): false | string | JwtPayload {
  try {
    return jwt.verify(token, secret);
  } catch (error) {
    console.error(error);
    return false;
  }
}

// logout route which requires token, adds to blacklist if so.
router.post('/logout', authenticateToken, (req: Request, res: Response) => {
  console.log('Logout user--------------->');
  try {
    const token = req.headers['authorization']
      ? req.headers['authorization']
      : req.cookies['authorization'];

    if (!checkBlacklist(token))
      loggedOutTokens.push({
        token,
        expires: Date.now() + 1000 * 60 * 60 * 24 * 30,
      });

    res.sendStatus(200);
  } catch (error) {
    console.error(error);
    res.sendStatus(500);
  }
});

// Check the blacklist for token.
export function checkBlacklist(token: String) {
  for (let i = loggedOutTokens.length - 1; i >= 0; i--) {
    if (loggedOutTokens[i].expires < Date.now()) loggedOutTokens.splice(i, 1);
    if (loggedOutTokens[i]?.token === token) return true;
  }
  return false;
}

export function setDatabase(new_database: Database) {
  database = new_database;
}

// get the users information if they are logged in.
router.get('/user', authenticateToken, async (req: Request, res: Response) => {
  console.log('Get user--------------->');

  try {
    const data = await database.searchForDataFromTable<Users>(
      Tables.USERS,
      'email',
      '=',
      req.user.email
    );

    if (data.length == 0)
      throw new BadParametersError('Email not exist', BadParameters.EMAIL);

    let user = data[0];

    res.send({
      id: user?.id,
      email: user?.email,
      password: user?.password,
      tiktok: user?.tiktok,
      instagram: user?.instagram,
      youtube: user?.youtube,
      facebook: user?.facebook,
      linkedin: user?.linkedin,
      plan: user?.plan,
    });
  } catch (error) {
    console.error(error);
    if (error instanceof BadParametersError) res.sendStatus(400);
    res.sendStatus(500);
  }
});

declare module 'express-serve-static-core' {
  export interface Request {
    user: any;
  }
}

export default router;
