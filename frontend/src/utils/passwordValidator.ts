/** Weak passwords that are explicitly forbidden */
const WEAK_PASSWORDS = new Set([
  "password",
  "password123",
  "password1234",
  "password12345",
  "123456",
  "1234567",
  "12345678",
  "123456789",
  "1234567890",
  "qwerty",
  "qwerty123",
  "qwerty1234",
  "abc123",
  "abcd1234",
  "admin",
  "admin123",
  "letmein",
  "welcome",
  "monkey",
  "dragon",
  "master",
  "login",
]);

const SPECIAL_CHARS = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~";

export interface PasswordValidationResult {
  valid: boolean;
  errors: string[];
}

/**
 * Validate password format - must be called on both frontend and backend.
 * Requirements:
 * - Minimum 8 characters
 * - At least one uppercase letter
 * - At least one lowercase letter
 * - At least one digit
 * - At least one special character
 * - Cannot be a known weak password
 */
export function validatePassword(password: string): PasswordValidationResult {
  const errors: string[] = [];

  if (password.length < 8) {
    errors.push("Password must be at least 8 characters long");
  }

  if (!/[A-Z]/.test(password)) {
    errors.push("Password must contain at least one uppercase letter");
  }

  if (!/[a-z]/.test(password)) {
    errors.push("Password must contain at least one lowercase letter");
  }

  if (!/[0-9]/.test(password)) {
    errors.push("Password must contain at least one digit");
  }

  const hasSpecialChar = [...password].some((char) => SPECIAL_CHARS.includes(char));
  if (!hasSpecialChar) {
    errors.push("Password must contain at least one special character (!@#$%^&*()_+-=[]{}|;':\",./<>?`~)");
  }

  if (WEAK_PASSWORDS.has(password.toLowerCase())) {
    errors.push("This password is too common. Please choose a stronger password");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
