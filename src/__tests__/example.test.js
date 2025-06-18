/**
 * @jest-environment jsdom
 */

describe('Example Test Suite', () => {
    it('should pass a simple test', () => {
        expect(true).toBe(true);
    });

    it('should test a simple function', () => {
        const sum = (a, b) => a + b;
        expect(sum(2, 3)).toBe(5);
    });
});
