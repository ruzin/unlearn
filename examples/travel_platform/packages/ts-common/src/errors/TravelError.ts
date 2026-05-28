export class TravelError extends Error {
  code: string;

  constructor(message: string, code: string = "travel/unknown") {
    super(message);
    this.name = "TravelError";
    this.code = code;
  }
}

export class AuthError extends TravelError {
  constructor(message: string) {
    super(message, "auth/forbidden");
    this.name = "AuthError";
  }
}

export class BookingError extends TravelError {
  constructor(message: string) {
    super(message, "booking/failed");
    this.name = "BookingError";
  }
}
