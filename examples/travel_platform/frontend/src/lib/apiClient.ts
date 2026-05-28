const GATEWAY = process.env.NEXT_PUBLIC_GATEWAY_URL ?? "http://gateway-bff";

export async function apiGet<T>(path: string, token?: string): Promise<T> {
  const res = await fetch(`${GATEWAY}${path}`, {
    headers: token ? { Authorization: token } : undefined,
  });
  if (!res.ok) throw new Error(`GET ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}

export async function apiPost<T>(path: string, body: unknown, token?: string): Promise<T> {
  const res = await fetch(`${GATEWAY}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: token } : {}),
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} failed: ${res.status}`);
  return (await res.json()) as T;
}
