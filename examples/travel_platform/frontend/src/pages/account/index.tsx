import { AccountHeader } from "../../components/account/AccountHeader";
import { PreferencesForm } from "../../components/account/PreferencesForm";
import { useAccount } from "../../hooks/useAccount";

export default function AccountPage() {
  const data = useAccount("usr_current") as { user: import("@travel/ts-common").User } | null;
  if (!data) return <p>Loading…</p>;
  return (
    <main>
      <AccountHeader user={data.user} />
      <PreferencesForm />
    </main>
  );
}
