import "./Cart.css";
import UserIcon from "./UserIcon";
import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import { apiFetch } from "./api";
import { money } from "./format";

export default function Cart(props) {
  const [users, setUsers] = useState([]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await apiFetch(`/carts/${props.cartId}/users`);
        setUsers(data);
      } catch (err) {
        console.error(err);
      }
    };

    if (props.cartId) {
      fetchUsers();
    }
    // membersKey changes when the cart is edited, so avatars refresh.
  }, [props.cartId, props.membersKey]);

  // const users = [
  //   { id: 1, name: "Alice Sharma" },
  //   { id: 2, name: "Bob Kumar" },
  //   { id: 3, name: "Charlie D'Souza" },
  //   { id: 4, name: "Diana Mehta" },
  //   { id: 5, name: "Ethan Reddy" },
  // ];
  return (
    // <Link to={`/cart/${props.key}`} className="default-cart cart-div">
    <div
      className={
        props.shared
          ? "default-cart cart-div cart-div-shared"
          : "default-cart cart-div"
      }
    >
      <div className="default-cart row1">
        <div className="default-cart col1">
          <Link
            to={`/cart/${props.cartId}`}
            state={{
              cartName: props.cartName,
              cartPrice: props.price,
              isShared: props.shared,
              cartDesc: props.cartDesc,
            }}
            className="default-cart cart-name"
          >
            {props.cartName}
          </Link>
          <div className="default-cart cart-desc">{props.cartDesc}</div>
        </div>
        <div className="default-cart col2">
          {props.onEdit && (
            <button
              type="button"
              className="default-cart edit-div"
              onClick={props.onEdit}
              title="Edit cart"
              aria-label={`Edit ${props.cartName}`}
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                fill="#2563eb"
                className="bi bi-pencil"
                viewBox="0 0 16 16"
              >
                <path d="M12.146.146a.5.5 0 0 1 .708 0l3 3a.5.5 0 0 1 0 .708l-10 10a.5.5 0 0 1-.168.11l-5 2a.5.5 0 0 1-.65-.65l2-5a.5.5 0 0 1 .11-.168zM11.207 2.5 13.5 4.793 14.793 3.5 12.5 1.207zm1.586 3L10.5 3.207 4 9.707V10h.5a.5.5 0 0 1 .5.5v.5h.5a.5.5 0 0 1 .5.5v.5h.293zm-9.761 5.175-.106.106-1.528 3.821 3.821-1.528.106-.106A.5.5 0 0 1 5 12.5V12h-.5a.5.5 0 0 1-.5-.5V11h-.5a.5.5 0 0 1-.468-.325" />
              </svg>
            </button>
          )}
          <div className="default-cart delete-div" onClick={props.onDelete}>
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
              fill="red"
              className="bi bi-trash"
              viewBox="0 0 16 16"
            >
              <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z" />
              <path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z" />
            </svg>
          </div>
        </div>
      </div>

      <div className="default-cart row2">
        <div className="default-cart row-2-col-1">
          <div className="default-cart price">{money(props.price)}</div>
        </div>

        <div className="default-cart row-2-col-2">
          {props.shared ? (
            <>
              <div className="default-cart shared-status-div">
                <div className="cart-status"></div>
                Shared
              </div>
              <div className="default-cart users">
                {users.map((user) => (
                  <UserIcon key={user.user_id} img={user.user_name} />
                ))}
              </div>
            </>
          ) : (
            <>
              <div className="default-cart shared-status-div"></div>
              <div className="default-cart users"></div>
            </>
          )}

          {/* <div className="default-cart users">
            {users.map((user) => (
              <UserIcon key={user.id} img={user.name} />
            ))}
          </div> */}

          <div className="default-cart datetime">
            {props.date ? props.date.split("T")[0] : ""}
          </div>
        </div>
      </div>
    </div>
    // </Link>
  );
}
