import { useState } from "react";

import { Button } from "../common/Button";

interface Props {
  onSubmit: (passenger: { firstName: string; lastName: string; dob: string }) => void;
}

export function PassengerForm({ onSubmit }: Props) {
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [dob, setDob] = useState("");
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit({ firstName, lastName, dob });
      }}
    >
      <input value={firstName} onChange={(e) => setFirstName(e.target.value)} placeholder="First name" />
      <input value={lastName} onChange={(e) => setLastName(e.target.value)} placeholder="Last name" />
      <input type="date" value={dob} onChange={(e) => setDob(e.target.value)} />
      <Button type="submit">Add passenger</Button>
    </form>
  );
}
