import { useEffect, useState } from "react";

import { apiGet } from "../lib/apiClient";
import { getToken } from "../lib/auth";

export function useAccount(userId: string) {
  const [data, setData] = useState<unknown>(null);
  useEffect(() => {
    if (!userId) return;
    apiGet(`/account/${userId}`, getToken() ?? undefined).then(setData);
  }, [userId]);
  return data;
}
