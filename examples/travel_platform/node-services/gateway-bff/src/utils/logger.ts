export const logger = {
  info: (msg: string) => console.log(`[gateway-bff] ${msg}`),
  warn: (msg: string) => console.warn(`[gateway-bff] ${msg}`),
  error: (msg: string) => console.error(`[gateway-bff] ${msg}`),
};
