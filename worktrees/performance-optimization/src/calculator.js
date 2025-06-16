/**
 * A simple calculator module with basic arithmetic operations.
 */

/**
 * Adds two numbers.
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The sum of a and b
 */
function add(a, b) {
  return a + b;
}

/**
 * Subtracts the second number from the first.
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The result of a - b
 */
function subtract(a, b) {
  return a - b;
}

/**
 * Multiplies two numbers.
 * @param {number} a - First number
 * @param {number} b - Second number
 * @returns {number} The product of a and b
 */
function multiply(a, b) {
  return a * b;
}

/**
 * Divides the first number by the second.
 * @param {number} a - Dividend
 * @param {number} b - Divisor (must not be zero)
 * @returns {number} The result of a / b
 * @throws {Error} If b is zero
 */
function divide(a, b) {
  if (b === 0) {
    throw new Error('Division by zero');
  }
  return a / b;
}

/**
 * Calculates the factorial of a number.
 * @param {number} n - A non-negative integer
 * @returns {number} The factorial of n
 * @throws {Error} If n is negative
 */
function factorial(n) {
  if (n < 0) {
    throw new Error('Factorial is not defined for negative numbers');
  }
  if (n === 0 || n === 1) {
    return 1;
  }
  return n * factorial(n - 1);
}

module.exports = {
  add,
  subtract,
  multiply,
  divide,
  factorial
};
