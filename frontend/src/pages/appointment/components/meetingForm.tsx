/**
 * External dependencies.
 */
import { useState } from "react";
import { useForm } from "react-hook-form";
import { motion } from "framer-motion";
import z from "zod";
import { useFrappePostCall } from "frappe-react-sdk";
import { zodResolver } from "@hookform/resolvers/zod";
import { CalendarPlus, ChevronLeft, CircleAlert, X } from "lucide-react";
import { formatDate } from "date-fns";
import { toast } from "sonner";
import { useSearchParams } from "react-router-dom";

/**
 * Internal dependencies.
 */
import { Button } from "@/components/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/form";
import { Input } from "@/components/input";
import Typography from "@/components/typography";
import { useAppContext } from "@/context/app";
import {
  getTimeZoneOffsetFromTimeZoneString,
  parseFrappeErrorMsg,
} from "@/lib/utils";
import { formatPhone, phoneGuide, readContactCookie, writeContactCookie } from "@/lib/booking-memory";
import Spinner from "@/components/spinner";

const contactFormSchema = z.object({
  firstName: z.string().trim().min(2, "Name must be at least 2 characters"),
  lastName: z.string().trim().min(2, "Last name must be at least 2 characters"),
  email: z.string().email("Please enter a valid email address"),
  phone: z.string().trim().refine((value) => {
    if (!value) return true;
    const digits = value.replace(/\D/g, "");
    return /^\+?[\d\s()-]+$/.test(value) && digits.length >= 7 && digits.length <= 15;
  }, "Enter a valid phone number"),
  guests: z.array(z.string().email("Please enter a valid email address")),
});

type ContactFormValues = z.infer<typeof contactFormSchema>;

interface MeetingFormProps {
  onBack: VoidFunction;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onSuccess: (data: any) => void;
  durationId: string;
  isMobileView: boolean;
}

const MeetingForm = ({
  onBack,
  durationId,
  onSuccess,
  isMobileView,
}: MeetingFormProps) => {
  const [isGuestsOpen, setIsGuestsOpen] = useState(false);
  const [guestInput, setGuestInput] = useState("");
  const { call: bookMeeting, loading } = useFrappePostCall(
    `frappe_appointment.api.personal_meet.book_time_slot`
  );
  const [searchParams] = useSearchParams();

  const { selectedDate, selectedSlot, timeZone } = useAppContext();
  const [savedContact] = useState(() => readContactCookie());

  const form = useForm<ContactFormValues>({
    resolver: zodResolver(contactFormSchema),
    defaultValues: {
      firstName: savedContact?.firstName ?? "",
      lastName: savedContact?.lastName ?? "",
      email: savedContact?.email ?? "",
      phone: savedContact?.phone ?? "",
      guests: [],
    },
  });

  const rememberedClass = (field: "firstName" | "lastName" | "email" | "phone") =>
    savedContact && !form.formState.dirtyFields[field]
      ? "bg-blue-50 dark:bg-blue-950/40"
      : "";

  const handleGuestKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addGuest();
    }
  };

  const addGuest = () => {
    const email = guestInput.trim();
    if (email && email.includes("@")) {
      const currentGuests = form.getValues("guests");
      if (!currentGuests.includes(email)) {
        form.setValue("guests", [...currentGuests, email]);
        setGuestInput("");
      }
    }
  };

  const removeGuest = (email: string) => {
    const currentGuests = form.getValues("guests");
    form.setValue(
      "guests",
      currentGuests.filter((guest) => guest !== email)
    );
  };
  const onSubmit = (data: ContactFormValues) => {
    const extraArgs: Record<string, string> = {};
    searchParams.forEach((value, key) => (extraArgs[key] = value));
    const meetingData = {
      ...extraArgs,
      duration_id: durationId,
      date: new Intl.DateTimeFormat("en-CA", {
        year: "numeric",
        month: "numeric",
        day: "numeric",
      }).format(selectedDate),
      user_timezone_offset: String(
        getTimeZoneOffsetFromTimeZoneString(timeZone)
      ),
      user_timezone: timeZone,
      start_time: selectedSlot.start_time,
      end_time: selectedSlot.end_time,
      user_name: `${data.firstName.trim()} ${data.lastName.trim()}`,
      user_email: data.email,
      user_phone: data.phone,
      other_participants: data.guests.join(", "),
    };

    bookMeeting(meetingData)
      .then((response) => {
        writeContactCookie({
          firstName: data.firstName.trim(),
          lastName: data.lastName.trim(),
          email: data.email.trim(),
          phone: data.phone,
        });
        onSuccess(response);
      })
      .catch((err) => {
        const error = parseFrappeErrorMsg(err);
        toast(error || "Something went wrong", {
          duration: 4000,
          classNames: {
            actionButton:
              "group-[.toast]:!bg-red-500 group-[.toast]:hover:!bg-red-300 group-[.toast]:!text-white",
          },
          icon: <CircleAlert className="h-5 w-5 text-red-500" />,
          action: {
            label: "OK",
            onClick: () => toast.dismiss(),
          },
        });
      });
  };

  return (
    <motion.div
      key={2}
      className={`w-full md:h-[38rem] lg:w-[41rem] shrink-0 md:p-6 md:px-4`}
      initial={isMobileView ? {} : { x: "100%" }}
      animate={{ x: 0 }}
      exit={isMobileView ? {} : { x: "100%" }}
      transition={{ duration: 0.2, ease: "easeInOut" }}
    >
      <Form {...form}>
        <form
          onSubmit={form.handleSubmit(onSubmit)}
          className="space-y-6 h-full flex justify-between flex-col"
        >
          <div className="space-y-4">
            <div className="flex gap-3 max-md:flex-col md:items-center md:justify-between">
              <Typography variant="p" className="text-2xl">
                Your contact info
              </Typography>
              <Typography className="text-sm  mt-1 text-blue-500 dark:text-blue-400">
                <CalendarPlus className="inline-block w-4 h-4 mr-1 md:hidden" />
                {formatDate(selectedDate, "d MMM, yyyy")}
              </Typography>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FormField
                control={form.control}
                name="firstName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel
                      className={`${
                        form.formState.errors.firstName ? "text-red-500" : ""
                      }`}
                    >
                      Name{" "}
                      <span className="text-red-500 dark:text-red-600">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        disabled={loading}
                        autoComplete="given-name"
                        className={`active:ring-blue-400 focus-visible:ring-blue-400 ${rememberedClass(
                          "firstName"
                        )} ${
                          form.formState.errors.firstName
                            ? "active:ring-red-500 focus-visible:ring-red-500"
                            : ""
                        }`}
                        placeholder="Ivan"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage
                      className={`${
                        form.formState.errors.firstName ? "text-red-500" : ""
                      }`}
                    />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="lastName"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel
                      className={`${
                        form.formState.errors.lastName ? "text-red-500" : ""
                      }`}
                    >
                      Last name{" "}
                      <span className="text-red-500 dark:text-red-600">*</span>
                    </FormLabel>
                    <FormControl>
                      <Input
                        disabled={loading}
                        autoComplete="family-name"
                        className={`active:ring-blue-400 focus-visible:ring-blue-400 ${rememberedClass(
                          "lastName"
                        )} ${
                          form.formState.errors.lastName
                            ? "active:ring-red-500 focus-visible:ring-red-500"
                            : ""
                        }`}
                        placeholder="Dorn"
                        {...field}
                      />
                    </FormControl>
                    <FormMessage
                      className={`${
                        form.formState.errors.lastName ? "text-red-500" : ""
                      }`}
                    />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="email"
              render={({ field }) => (
                <FormItem>
                  <FormLabel
                    className={`${
                      form.formState.errors.email ? "text-red-500" : ""
                    }`}
                  >
                    Email{" "}
                    <span className="text-red-500 dark:text-red-600">*</span>
                  </FormLabel>
                  <FormControl>
                    <Input
                      disabled={loading}
                      className={`active:ring-blue-400 focus-visible:ring-blue-400 ${rememberedClass(
                        "email"
                      )} ${
                        form.formState.errors.email
                          ? "active:ring-red-500 focus-visible:ring-red-500"
                          : ""
                      }`}
                      placeholder="john.Doe@gmail.com"
                      {...field}
                    />
                  </FormControl>
                  <FormMessage
                    className={`${
                      form.formState.errors.email ? "text-red-500" : ""
                    }`}
                  />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel
                    className={`${
                      form.formState.errors.phone ? "text-red-500" : ""
                    }`}
                  >
                    Phone
                  </FormLabel>
                  <FormControl>
                    <Input
                      disabled={loading}
                      type="tel"
                      inputMode="tel"
                      autoComplete="tel"
                      className={`active:ring-blue-400 focus-visible:ring-blue-400 ${rememberedClass(
                        "phone"
                      )} ${
                        form.formState.errors.phone
                          ? "active:ring-red-500 focus-visible:ring-red-500"
                          : ""
                      }`}
                      placeholder="+971 52 518 6181"
                      {...field}
                      onChange={(event) => field.onChange(formatPhone(event.target.value))}
                    />
                  </FormControl>
                  <PhoneGuide value={field.value} />
                  <FormMessage
                    className={`${
                      form.formState.errors.phone ? "text-red-500" : ""
                    }`}
                  />
                </FormItem>
              )}
            />

            <div className="space-y-2">
              <Button
                type="button"
                variant="ghost"
                className="h-auto hover:bg-blue-50 dark:hover:bg-blue-800/10 text-blue-500 dark:text-blue-400 hover:text-blue-600 "
                onClick={() => setIsGuestsOpen(!isGuestsOpen)}
                disabled={loading}
              >
                {isGuestsOpen ? "Hide Guests" : "+ Add Guests"}
              </Button>

              {isGuestsOpen && (
                <div className="space-y-2">
                  <Input
                    placeholder="janedoe@hotmail.com, bob@gmail.com, etc."
                    value={guestInput}
                    className="active:ring-blue-400 focus-visible:ring-blue-400"
                    onChange={(e) => setGuestInput(e.target.value)}
                    onKeyDown={handleGuestKeyDown}
                    onBlur={addGuest}
                    disabled={loading}
                  />
                  <div className="flex flex-wrap gap-2">
                    {form.watch("guests").map((guest) => (
                      <div
                        key={guest}
                        className="flex items-center gap-1 px-2 py-1 bg-blue-500 dark:bg-blue-400 text-white dark:text-background rounded-full text-sm"
                      >
                        <span>{guest}</span>
                        <button
                          type="button"
                          onClick={() => removeGuest(guest)}
                          className="hover:text-blue-200"
                        >
                          <X className="h-3 w-3 dark:text-background" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>

          <div className="flex justify-between md:pt-4 max-md:h-14 max-md:fixed max-md:bottom-0 max-md:left-0 max-md:w-screen max-md:border max-md:z-10 max-md:bg-background max-md:border-top max-md:items-center max-md:px-4">
            <Button
              type="button"
              className="text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-400 md:hover:bg-blue-50 md:dark:hover:bg-blue-800/10 max-md:px-0 max-md:hover:underline max-md:hover:bg-transparent"
              onClick={onBack}
              variant="ghost"
              disabled={loading}
            >
              <ChevronLeft /> Back
            </Button>
            <Button
              disabled={loading}
              className="bg-blue-500 dark:bg-blue-400 hover:bg-blue-500 dark:hover:bg-blue-400"
              type="submit"
            >
              {loading && <Spinner />} Schedule Meeting
            </Button>
          </div>
        </form>
      </Form>
    </motion.div>
  );
};

const PhoneGuide = ({ value }: { value: string }) => {
  const marks = phoneGuide(value);
  if (!marks) return null;
  return (
    <p className="text-sm tracking-wide" aria-hidden="true">
      {marks.map((mark, index) => (
        <span
          key={`${mark.state}-${index}`}
          className={
            mark.state === "filled"
              ? "font-medium text-blue-600 dark:text-blue-400"
              : mark.state === "empty"
                ? "text-zinc-300 dark:text-zinc-600"
                : "text-muted-foreground"
          }
        >
          {mark.char}
        </span>
      ))}
    </p>
  );
};

export default MeetingForm;
