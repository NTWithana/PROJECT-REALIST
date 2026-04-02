export type ChatSignal = {
  id: string;
  domain: string;
  summary: string;
  pattern: string;
  confidence: number;
  sourceSessionId: string;
};
