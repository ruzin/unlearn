export const logger = {
  info: (msg: string) => console.log(`[notify] ${msg}`),
  error: (msg: string) => console.error(`[notify] ${msg}`),
};
