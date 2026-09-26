const COOKIE = "fa_contact";
const CHOICE_COOKIE = "fa_cookie_choice";
const MAX_AGE_SECONDS = 60 * 60 * 24 * 180;
const CHOICE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

export const COOKIE_CHOICE_EVENT = "fa-cookie-choice";
export const COOKIE_SETTINGS_EVENT = "fa-cookie-settings";

export type CookieChoice = "allow" | "deny";

export type SavedContact = {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
};

export function formatPhone(input: string): string {
  let raw = input.replace(/[^\d+]/g, "");
  if (raw.startsWith("00")) raw = `+${raw.slice(2)}`;
  let digits = raw.replace(/\D/g, "").slice(0, 15);
  if (!digits) return raw.startsWith("+") ? "+" : "";
  if (digits.startsWith("0")) digits = `971${digits.slice(1)}`.slice(0, 15);
  if (digits.startsWith("971")) {
    const national = digits.slice(3, 12);
    const parts = [national.slice(0, 2), national.slice(2, 5), national.slice(5, 9)].filter(Boolean);
    return ["+971", ...parts].join(" ");
  }
  const groups: string[] = [];
  for (let i = 0; i < digits.length; i += 3) groups.push(digits.slice(i, i + 3));
  return `+${groups.join(" ")}`;
}

export type PhoneMark = { char: string; state: "fixed" | "filled" | "empty" };

/** UAE shape +971 52 518 6181. Empty slots stay visible so the next digit is obvious. */
export function phoneGuide(value: string): PhoneMark[] | null {
  const digits = value.replace(/\D/g, "");
  if (digits && !digits.startsWith("971") && !digits.startsWith("0")) return null;
  const national = digits.startsWith("971") ? digits.slice(3) : digits.startsWith("0") ? digits.slice(1) : "";
  const marks: PhoneMark[] = "+971 ".split("").map((char) => ({ char, state: "fixed" }));
  const groups = [2, 3, 4];
  let index = 0;
  groups.forEach((length, group) => {
    if (group) marks.push({ char: " ", state: "fixed" });
    for (let n = 0; n < length; n += 1) {
      const digit = national[index];
      index += 1;
      marks.push(digit ? { char: digit, state: "filled" } : { char: "·", state: "empty" });
    }
  });
  return marks;
}

function readCookieValue(name: string): string | null {
  if (typeof document === "undefined") return null;
  const pair = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));
  if (!pair) return null;
  return decodeURIComponent(pair.slice(name.length + 1));
}

export function readCookieChoice(): CookieChoice | null {
  const value = readCookieValue(CHOICE_COOKIE);
  return value === "allow" || value === "deny" ? value : null;
}

export function clearContactCookie() {
  if (typeof document === "undefined") return;
  document.cookie = `${COOKIE}=; Path=/schedule; Max-Age=0; SameSite=Lax; Secure`;
}

export function writeCookieChoice(choice: CookieChoice) {
  if (typeof document === "undefined") return;
  document.cookie = `${CHOICE_COOKIE}=${choice}; Path=/schedule; Max-Age=${CHOICE_MAX_AGE_SECONDS}; SameSite=Lax; Secure`;
  if (choice === "deny") clearContactCookie();
  window.dispatchEvent(new CustomEvent(COOKIE_CHOICE_EVENT, { detail: choice }));
}

export function readContactCookie(): SavedContact | null {
  if (readCookieChoice() !== "allow") return null;
  const raw = readCookieValue(COOKIE);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<SavedContact>;
    if (!parsed || typeof parsed !== "object") return null;
    return {
      firstName: String(parsed.firstName || ""),
      lastName: String(parsed.lastName || ""),
      email: String(parsed.email || ""),
      phone: formatPhone(String(parsed.phone || "")),
    };
  } catch {
    return null;
  }
}

export function writeContactCookie(contact: SavedContact) {
  if (typeof document === "undefined" || readCookieChoice() !== "allow") return;
  const value = encodeURIComponent(JSON.stringify(contact));
  document.cookie = `${COOKIE}=${value}; Path=/schedule; Max-Age=${MAX_AGE_SECONDS}; SameSite=Lax; Secure`;
}
