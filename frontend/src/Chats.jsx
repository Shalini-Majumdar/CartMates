import "./Chats.css";

export default function Chats(props) {
  const userId = localStorage.getItem("userId");
  return (
    <>
      <div
        className={
          String(props.senderId) === String(userId)
            ? "default-chat message-div-receive"
            : "default-chat message-div"
        }
      >
        <div className="default-chat msg-user">
          {props.sendType === "assistant" ? (
            // A robot, so the assistant is never mistaken for a person's initials.
            <span className="user-avatar bot-avatar" title="Shopping assistant">
              <svg
                viewBox="0 0 24 24"
                width="22"
                height="22"
                fill="currentColor"
                aria-hidden="true"
              >
                <path d="M12 2a1.5 1.5 0 0 1 .75 2.8V6H17a3 3 0 0 1 3 3v8a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3V9a3 3 0 0 1 3-3h4.25V4.8A1.5 1.5 0 0 1 12 2ZM9 10.5a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3Zm6 0a1.5 1.5 0 1 0 0 3 1.5 1.5 0 0 0 0-3ZM9 16a.75.75 0 0 0 0 1.5h6a.75.75 0 0 0 0-1.5H9ZM2 11a1 1 0 0 1 1 1v3a1 1 0 1 1-2 0v-3a1 1 0 0 1 1-1Zm20 0a1 1 0 0 1 1 1v3a1 1 0 1 1-2 0v-3a1 1 0 0 1 1-1Z" />
              </svg>
            </span>
          ) : (
            <img
              src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
                props.user
              )}&padding=15&fontSize=36`}
              alt={props.user}
              className="user-avatar"
            />
          )}
        </div>
        <div className="default-chat message">{props.chat}</div>
      </div>
    </>
  );
}
