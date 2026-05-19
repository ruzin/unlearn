// All exports here are never imported elsewhere — dead code.

export function legacyParser(input: string): string[] {
  return input.split(",");
}

export function legacyFormatter(value: number): string {
  return `${value}`;
}
