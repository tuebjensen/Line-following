export function* createCounter() {
    for (let i = 0; ; i++) {
        yield i
    }
}