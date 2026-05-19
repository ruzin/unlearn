export interface UserType {
  id: number;
  email: string;
  name: string;
}

export function makeUser(id: number, email: string): UserType {
  return { id, email, name: email.split("@")[0] };
}
