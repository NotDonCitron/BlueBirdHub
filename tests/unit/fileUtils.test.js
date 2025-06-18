const { formatFileSize } = require('../../src/utils/fileUtils');

describe('File Utilities', () => {
  test('formatFileSize converts bytes to human readable format', () => {
    expect(formatFileSize(0)).toBe('0 Bytes');
    expect(formatFileSize(500)).toBe('500 Bytes');
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1500000)).toBe('1.43 MB');
    expect(formatFileSize(1500000000)).toBe('1.4 GB');
  });
});
