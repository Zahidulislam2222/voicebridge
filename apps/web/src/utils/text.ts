// Fixed Unicode/ASCII control syntax, independent of product configuration.
export function containsInvalidPlainText(text: string): boolean {
  return Array.from(text).some((character) => {
    const code = character.charCodeAt(0);
    return (code < 32 && ![9, 10, 13].includes(code)) || code === 65533;
  });
}
