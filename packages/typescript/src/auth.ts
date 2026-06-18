const BASE_URLS: Record<string, string> = {
  live: "https://api.kiwoom.com",
  mock: "https://mockapi.kiwoom.com",
};

interface TokenResponse {
  token_type: string;
  access_token: string;
  expires_dt: string; // "YYYYMMDDHHMMSS"
}

let cachedToken: string | null = null;
let expiresAt: number = 0;

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
  const env = (process.env.KIWOOM_ENV || "mock").toLowerCase();
  return BASE_URLS[env] ?? BASE_URLS.mock;
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
    throw new Error(
      "KIWOOM_APP_KEY and KIWOOM_APP_SECRET environment variables are required"
    );
  }

  const base = getBaseUrl();
  const res = await fetch(`${base}/oauth2/token/au10001`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ grant_type: "client_credentials", appkey: appKey, appsecretkey: appSecret }),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Token fetch failed (${res.status}): ${text}`);
  }

  const data = (await res.json()) as TokenResponse;
  cachedToken = data.access_token;
  expiresAt = parseExpiresDt(data.expires_dt);
  return cachedToken;
}
