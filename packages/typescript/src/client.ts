import { getToken, getBaseUrl } from "./auth.js";

export interface KiwoomResponse {
  [key: string]: unknown;
}

export async function callKiwoom(
  realPath: string,
  apiId: string,
  body: Record<string, unknown>
): Promise<KiwoomResponse> {
  const token = await getToken();
  const base = getBaseUrl();

  const res = await fetch(`${base}${realPath}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      "api-id": apiId,
    },
    body: JSON.stringify(body),
  });

  const data = (await res.json()) as KiwoomResponse;

  if (!res.ok) {
    throw new Error(
      `Kiwoom API error (${res.status}): ${JSON.stringify(data)}`
    );
  }

  return data;
}
