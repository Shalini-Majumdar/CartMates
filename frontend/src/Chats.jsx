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
          <img
            src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
              props.user
            )}&padding=15&fontSize=36`}
            alt={props.user}
            className="user-avatar"
          />
        </div>
        <div className="default-chat message">{props.chat}</div>
      </div>
    </>
  );
}
