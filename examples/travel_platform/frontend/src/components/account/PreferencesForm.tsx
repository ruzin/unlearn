import { useState } from "react";

import { Button } from "../common/Button";

export function PreferencesForm() {
  const [newsletter, setNewsletter] = useState(false);
  return (
    <form>
      <label>
        <input type="checkbox" checked={newsletter} onChange={(e) => setNewsletter(e.target.checked)} />
        Subscribe to newsletter
      </label>
      <Button type="submit">Save</Button>
    </form>
  );
}
