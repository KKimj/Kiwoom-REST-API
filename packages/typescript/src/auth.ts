const BASE_URLS: Record<string, string> = {
  live: "https://api.kiwoom.com",
  mock: "https://mockapi.kiwoom.com",
};

interface TokenResponse {
  token_type: string;
  token: string;
  expires_dt: string; // "YYYYMMDDHHMMSS"
  return_code: number;
  return_msg: string;
}

let cachedToken: string | null = null;
let expiresAt = 0;

function parseExpiresDt(dt: string): number {
  // "20251231235959" → ms timestamp
  const y = +dt.slice(0, 4);
  const mo = +dt.slice(4, 6) - 1;
  const d = +dt.slice(6, 8);
  const h = +dt.slice(8, 10);
  const mi = +dt.slice(10, 12);
  const s = +dt.slice(12, 14);
  return new Date(y, mo, d, h, mi, s).getTime();
}

export function getBaseUrl(): string {
  const env = (process.env.KIWOOM_ENV ?? "mock").toLowerCase();
  return env === "live" ? BASE_URLS.live : BASE_URLS.mock;
}

export async function getToken(): Promise<string> {
  if (process.env.KIWOOM_ACCESS_TOKEN) {
    return process.env.KIWOOM_ACCESS_TOKEN;
  }

  const now = Date.now();
  // refresh 5 minutes before expiry
  if (cachedToken && now < expiresAt - 5 * 60 * 1000) {
    return cachedToken;
  }

  const appKey = process.env.KIWOOM_APP_KEY;
  const appSecret = process.env.KIWOOM_APP_SECRET;
  if (!appKey || !appSecret) {
    throw new Error("KIWOOM_APP_KEY and KIWOOM_APP_SECRET environment variables are required");
  }

  const base = getBaseUrl();
  const res = await fetch(`${base}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "api-id": "au10001" },
    body: JSON.stringify({
      grant_type: "client_credentials",
      appkey: appKey,
      secretkey: appSecret,
    }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Token fetch failed (${res.status}): ${text}`);
  }

  const data = (await res.json()) as TokenResponse;
  if (data.return_code !== 0) {
    throw new Error(`Token fetch failed: ${data.return_msg}`);
  }
  cachedToken = data.token;
  expiresAt = parseExpiresDt(data.expires_dt);
  return cachedToken;
}
