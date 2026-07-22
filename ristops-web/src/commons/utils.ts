/** Trim a string and collapse empty/whitespace-only values to `null`. */
export function orNull(s: string): string | null {
  return s.trim() || null;
}

/**
 * Page through a paginated fetcher to completion and return the flattened items. For the
 * cases where a caller needs the *complete* bounded result set rather than one page at a
 * time — a single request when everything fits in a page, looping only when it doesn't.
 */
export async function collectAllPages<TItem>(
  fetchPage: (
    page: number,
    pageSize: number,
  ) => Promise<{ items: TItem[]; totalPages: number }>,
  pageSize = 100,
): Promise<TItem[]> {
  const items: TItem[] = [];
  let page = 0;
  let totalPages = 1;
  do {
    const result = await fetchPage(page, pageSize);
    items.push(...result.items);
    totalPages = result.totalPages;
    page += 1;
  } while (page < totalPages);
  return items;
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
