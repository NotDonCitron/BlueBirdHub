function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  const size = parseFloat((bytes / Math.pow(k, i)).toFixed(2));
  
  // Remove trailing zeros and decimal point if not needed
  const formattedSize = size % 1 === 0 ? size.toString() : size.toString();
  
  return `${formattedSize} ${sizes[i]}`;
}

module.exports = {
  formatFileSize
};