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

/**
 * Avatar initials: the first character of up to the first two alphanumeric tokens,
 * splitting on any run of non-alphanumeric characters. Falls back to the first
 * character when the name has no alphanumeric content.
 *
 *   "House Targaryen" -> "HT"   "Restaurant.212" -> "R2"
 *   "Restaurant .212" -> "R2"   "MyRestaurant"   -> "M"   "." -> "."
 */
export function initials(name: string): string {
  const tokens = name.split(/[^a-zA-Z0-9]+/).filter(Boolean);
  if (tokens.length === 0) return name.trim().charAt(0);
  return tokens
    .slice(0, 2)
    .map((token) => token.charAt(0).toUpperCase())
    .join('');
}
