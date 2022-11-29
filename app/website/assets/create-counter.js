/**
 * Yields number from 0 to infinity, one-by-one.
 * @returns {Generator<number, never, void>}
 */
export function* createCounter() {
    for (let i = 0; ; i++) {
        yield i
    }
}