import type { User } from "@travel/ts-common";

export function AccountHeader({ user }: { user: User }) {
  return (
    <header className="account-header">
      <h1>{user.fullName}</h1>
      <p>{user.email}</p>
      {user.loyaltyTier && <span className={`tier tier-${user.loyaltyTier}`}>{user.loyaltyTier}</span>}
    </header>
  );
}
