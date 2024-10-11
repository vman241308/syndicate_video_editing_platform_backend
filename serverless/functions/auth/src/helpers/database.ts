import { Client } from "pg";
import EventEmitter from "events";

export enum Events {
  ERROR = "error",
  CONNECTED = "connected",
}

// Database class which can emit two events connected and error.
export class Database extends EventEmitter {
  client!: Client;

  constructor() {
    super();
    this.connect();
  }

  // connects to the database using the information in google secrets manager. Assumes postgres database. Reconnects if error.
  async connect() {
    console.log(`Connecting to client`);
    this.client = new Client({
      host: process.env.DB_HOST,
      port: parseInt(process.env.DB_PORT!),
      database: process.env.DB_DATABASE,
      user: process.env.DB_USER,
      password: process.env.DB_PASSWORD,
    });

    const startedAt = new Date().getTime();

    this.client.on("error", (err) => {
      console.log("An error occurred with client => ", err);

      console.log("Started at:", startedAt);
      console.log("Crashed at:", new Date().getTime());

      this.emit(Events.ERROR);
    });

    this.client.connect((err) => {
      if (err) {
        console.log(`[main] Connection error => ${err}`);
        this.emit(Events.ERROR);
      } else {
        console.log(`[main] Connected to database!`);
        this.emit(Events.CONNECTED);
      }
    });
  }

  // Pulls dadta from data with specific condition.
  async searchForDataFromTable<T extends Table>(
    table: Tables,
    column: keyof T,
    conditional: Conditional,
    condition: string
  ): Promise<T[]> {
    let result = await this.client.query(
      `SELECT * FROM ${table} WHERE ${column.toString()} ${conditional} $1`,
      [condition]
    );
    return result.rows as T[];
  }

  // Returns all data from the specified table.
  async getAllFromTable<T extends Table>(table: string): Promise<T[]> {
    let result = await this.client.query(`SELECT * FROM ${table}`);
    return result.rows as T[];
  }

  // Adds row into the table of your choosing
  async addRowIntoTable<T extends Table>(
    table: Tables,
    dataObject: T
  ): Promise<number | boolean> {
    try {
      let names = [];
      let values = [];
      let placeholders = [];
      let i = 1;

      // makes the data object have sanitization
      for (const [key, value] of Object.entries(dataObject)) {
        names.push(key);
        placeholders.push(`$${i++}`);
        values.push(value);
      }

      let result = await this.client.query(
        `INSERT INTO ${table}(${names.join()}) VALUES (${placeholders.join()}) RETURNING *;`,
        values
      );

      return result.rows[0].id;
    } catch (error) {
      console.error("addRowIntoTable error", error);
      return false;
    }
  }

  // Update the specified rows to have a new dataObject, can be partial.
  async updateRowInTable<T extends Table>(
    table: Tables,
    column: keyof T,
    conditional: Conditional,
    condition: string,
    dataObject: Partial<T>
  ) {
    try {
      let names = [];
      let values = [];
      let i = 1;

      // makes the data object have sanitization
      for (const [key, value] of Object.entries(dataObject)) {
        names.push(`${key} = $${i++}`);
        values.push(value);
      }

      values.push(condition);

      await this.client.query(
        `UPDATE ${table} SET ${names.join()} WHERE ${column.toString()} ${conditional} $${i};`,
        values
      );

      return true;
    } catch (error) {
      console.error(error);
      return false;
    }
  }

  // Delete a row in a table. Can take multiple conditions, using a ConditionalObject array/
  async deleteRowsInTable(table: Tables, conditions: ConditionalObject[]) {
    try {
      let conditionsString = "";
      let conditionArray: string[] = [];

      let i;

      for (i = 0; i < conditions.length - 1; i++) {
        const { column, conditional, condition } = conditions[i];

        conditionsString += `${column} ${conditional} $${i + 1} AND `;
        conditionArray.push(condition);
      }

      const { column, conditional, condition } =
        conditions[conditions.length - 1];
      conditionsString += `${column} ${conditional} $${conditions.length}`;
      conditionArray.push(condition);

      await this.client.query(
        `DELETE FROM ${table} WHERE ${conditionsString};`,
        conditionArray
      );

      return true;
    } catch (error) {
      console.error(error);
      return false;
    }
  }
}

export interface ConditionalObject {
  column: string;
  conditional: Conditional;
  condition: string;
}

// Update the table structures bellow whenever there is a change in the database.
// User table structure
export interface Users {
  id?: number;
  email: string;
  password: string;
  instagram?: boolean;
  tiktok?: boolean;
  facebook?: boolean;
  youtube?: boolean;
  linkedin?: boolean;
  plan?: string;
}

// All possible conditons for the query.
export type Conditional =
  | "="
  | ">"
  | "<"
  | ">="
  | "<="
  | "<>"
  | "BETWEEN"
  | "LIKE"
  | "IN"
  | "!=";

// Table structures, update to reflect the database structure.
export type Table = Users;
export enum Tables {
  USERS = "users",
}
