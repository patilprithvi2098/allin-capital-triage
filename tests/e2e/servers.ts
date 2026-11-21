// Test servers. OPEN: no logins (Riya's screen, all calls stubbed). LOGIN: two logins with test-only passwords,
// generated for these tests and used nowhere else.
export const OPEN_PORT = 8332;
export const LOGIN_PORT = 8333;
export const TEST_PW = { riya: "e2e-riya-only", kushal: "e2e-kushal-only" };
export const LOGIN_BASE = `http://127.0.0.1:${LOGIN_PORT}`;
