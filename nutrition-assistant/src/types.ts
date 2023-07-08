export class Success<R> {
  kind: string = "success";
  value: R;
  constructor(r: R) {
    this.value = r;
  }
}

export class Failure<E> {
  kind: string = "failure";
  value: E;
  constructor(e: E) {
    this.value = e;
  }
}

export type Either<R, E> = Success<R> | Failure<E>;

export type Recipe = {
  total_servings: number,
  ingredients: {units: string, "name": string, "total": number}[],
  instructions: string,
};

