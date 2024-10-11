// Possible errors for bad parameters, update this if you wish to add another.
export enum BadParameters {
	DEFAULT = 'default',
	BODY = 'body',
	PASSWORD = 'password',
	EMAIL = 'email',
	EXISTS = 'exists',
	FORBIDDEN = 'forbidden',
	INVALID = 'invalid'
}

// Creates an error, with the BadParameters type, and returns the type upon the method call getType;
export default class BadParametersError extends Error {
	badParameterType: BadParameters = BadParameters.DEFAULT;

	constructor(msg: string, type?: BadParameters) {
		super(msg);
		if (type) this.badParameterType = type;
	}

	getType() {
		return this.badParameterType;
	}
}
