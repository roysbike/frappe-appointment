import { useEffect, useState } from "react";

import { Button } from "@/components/button";
import {
  COOKIE_SETTINGS_EVENT,
  readCookieChoice,
  writeCookieChoice,
  type CookieChoice,
} from "@/lib/booking-memory";

const CookieNotice = () => {
  const [choice, setChoice] = useState<CookieChoice | null>(() => readCookieChoice());
  const [open, setOpen] = useState(() => readCookieChoice() === null);

  useEffect(() => {
    const show = () => setOpen(true);
    window.addEventListener(COOKIE_SETTINGS_EVENT, show);
    return () => window.removeEventListener(COOKIE_SETTINGS_EVENT, show);
  }, []);

  if (!open) return null;

  const choose = (next: CookieChoice) => {
    writeCookieChoice(next);
    setChoice(next);
    setOpen(false);
  };

  return (
    <div
      role="dialog"
      aria-labelledby="cookie-notice-title"
      className="fixed z-50 bottom-20 left-3 right-3 md:bottom-4 md:left-auto md:right-4 md:w-[28rem] rounded-2xl border border-gray-200 dark:border-gray-600 bg-background shadow-lg p-4 space-y-3"
    >
      <div className="space-y-2">
        <p id="cookie-notice-title" className="font-semibold">
          Cookies
        </p>
        {choice && (
          <p className="text-sm text-muted-foreground">
            {choice === "allow"
              ? "Saving your contact details on this device is on."
              : "Saving your contact details on this device is off."}
          </p>
        )}
        <p className="text-sm text-muted-foreground">
          This page can store your name, email and phone in a cookie for 180 days,
          only to fill this form the next time you book. It is not used for
          advertising and is not shared with other sites. UAE Federal Decree-Law
          No. 45 of 2021 requires this choice before those details are saved. The
          browser can still remember what you type if you choose No thanks.
        </p>
      </div>
      <div className="flex gap-2">
        <Button
          type="button"
          className="flex-1 bg-blue-500 dark:bg-blue-400 hover:bg-blue-500 dark:hover:bg-blue-400"
          onClick={() => choose("allow")}
        >
          Allow
        </Button>
        <Button type="button" variant="outline" className="flex-1" onClick={() => choose("deny")}>
          No thanks
        </Button>
      </div>
    </div>
  );
};

export default CookieNotice;
