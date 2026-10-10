export default function UserIcon(props) {
  return (
    <>
      <div className="default-cart user-icon-cart">
        <img
          src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
            props.img
          )}&padding=20&fontSize=36`}
          alt={props.img}
        />
      </div>
    </>
  );
}
