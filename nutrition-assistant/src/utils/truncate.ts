export function truncate(n: number, digits: number): number {
  const m = 10 * digits;
  return Math.floor(n * m)/m;
}
