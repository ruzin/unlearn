import type { CurrencyCode } from "./money";

export interface User {
  id: string;
  email: string;
  fullName: string;
  homeCurrency: CurrencyCode;
  loyaltyTier?: "bronze" | "silver" | "gold" | "platinum";
}

export interface UserPreferences {
  newsletter: boolean;
  preferredAirports: string[];
  seatPreference?: "window" | "aisle";
}
