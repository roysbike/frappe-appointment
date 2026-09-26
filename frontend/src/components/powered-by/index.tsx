import Typography from "../typography";

const PoweredBy = ({ onCookieSettings }: { onCookieSettings?: () => void }) => {
  return (
    <>
      <div className="flexitems-center w-full justify-center shrink-0">
        <Typography
          variant="h5"
          className="flex items-center py-5 max-md:pb-20 max-lg:py-2 justify-center gap-1"
        >
          <Typography variant="p"> Powered by</Typography>
          <Typography variant="p">
            <a
              href="https://github.com/roysbike/frappe-appointment/"
              target="_blank"
              rel="noopener noreferrer"
              className="font-semibold hover:underline text-blue-400"
            >
              Frappe Appointment
            </a>
          </Typography>
          {onCookieSettings && (
            <button
              type="button"
              onClick={onCookieSettings}
              className="font-semibold hover:underline text-blue-400"
            >
              Cookies
            </button>
          )}
        </Typography>
      </div>
    </>
  );
};

export default PoweredBy;
