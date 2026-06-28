/** Trim a string and collapse empty/whitespace-only values to `null`. */
export function orNull(s: string): string | null {
  return s.trim() || null;
}

/** Case-insensitive `contains` match against an option's label (falling back to its value). */
export function matchOption(
  input: string,
  option?: { value?: string | number; label?: string },
): boolean {
  return String(option?.label ?? option?.value ?? '')
    .toLowerCase()
    .includes(input.toLowerCase());
}
