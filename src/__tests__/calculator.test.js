const { add, subtract, multiply, divide, factorial } = require('../calculator');

describe('Calculator', () => {
  // Test addition
  describe('add()', () => {
    it('should add two positive numbers correctly', () => {
      expect(add(5, 3)).toBe(8);
    });

    it('should add negative numbers correctly', () => {
      expect(add(-1, -1)).toBe(-2);
    });

    it('should handle zero correctly', () => {
      expect(add(0, 5)).toBe(5);
      expect(add(5, 0)).toBe(5);
    });
  });

  // Test subtraction
  describe('subtract()', () => {
    it('should subtract two numbers correctly', () => {
      expect(subtract(10, 4)).toBe(6);
    });

    it('should handle negative results', () => {
      expect(subtract(5, 10)).toBe(-5);
    });
  });

  // Test multiplication
  describe('multiply()', () => {
    it('should multiply two numbers correctly', () => {
      expect(multiply(3, 4)).toBe(12);
    });

    it('should return 0 when multiplying by zero', () => {
      expect(multiply(5, 0)).toBe(0);
      expect(multiply(0, 5)).toBe(0);
    });
  });

  // Test division
  describe('divide()', () => {
    it('should divide two numbers correctly', () => {
      expect(divide(10, 2)).toBe(5);
    });

    it('should handle decimal results', () => {
      expect(divide(5, 2)).toBe(2.5);
    });

    it('should throw error when dividing by zero', () => {
      expect(() => divide(10, 0)).toThrow('Division by zero');
    });
  });

  // Test factorial
  describe('factorial()', () => {
    it('should calculate factorial of 0', () => {
      expect(factorial(0)).toBe(1);
    });

    it('should calculate factorial of 1', () => {
      expect(factorial(1)).toBe(1);
    });

    it('should calculate factorial of positive numbers', () => {
      expect(factorial(5)).toBe(120);
      expect(factorial(6)).toBe(720);
    });

    it('should throw error for negative numbers', () => {
      expect(() => factorial(-1)).toThrow('Factorial is not defined for negative numbers');
    });
  });

  // Test edge cases
  describe('Edge Cases', () => {
    it('should handle large numbers', () => {
      const largeNumber = Number.MAX_SAFE_INTEGER;
      expect(add(largeNumber, 1)).toBe(largeNumber + 1);
    });

    it('should handle decimal numbers', () => {
      expect(add(0.1, 0.2)).toBeCloseTo(0.3);
    });
  });
});


