import { Either, Success, Failure } from '../types';

function parse<R>(s: string): Either<R, Error> {
  try {
    const result = JSON.parse(s);
    return new Success(result);
  } catch (error: any) {
    console.error(`Failed to parse string as JSON`, error);
    return new Failure(error);
  }
};

export default parse;
