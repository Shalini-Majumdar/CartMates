import "./SelectedCart.css";
import Product from "./Product";
import { useState, useEffect, useCallback } from "react";
import { useParams, useLocation, useNavigate } from "react-router-dom";
import ErrorPopup from "./Error";
import Chats from "./Chats";
import { apiFetch } from "./api";

export default function SelectedCart(props) {
  const userId = localStorage.getItem("userId");
  const userName = localStorage.getItem("userName");
  const location = useLocation();
  const navigate = useNavigate();
  const { cartId } = useParams();
  const [cartItems, setCartItems] = useState([]);
  // Router state is only present when navigating from the cart list; on a
  // direct visit or a hard refresh we have to fetch the cart ourselves.
  const [cartInfo, setCartInfo] = useState(() => location.state || null);
  const { cartName, cartPrice, isShared, cartDesc } = cartInfo || {};
  const [loading, setLoading] = useState(true);
  const [chatMessage, setChatMessage] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [isSending, setIsSending] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [users, setUsers] = useState([]);
  const [totalCost, setTotalCost] = useState(null);

  //To fetch all products for the selected cart------------------

  const fetchProducts = useCallback(async () => {
    try {
      const data = await apiFetch(`/carts/${cartId}/items`);
      setCartItems(data);
    } catch (err) {
      setErrorMessage(err.message || "Something went wrong");
      setCartItems([]);
    }
  }, [cartId]);

  const fetchMessages = useCallback(async () => {
    try {
      const data = await apiFetch(`/messages/${cartId}`);
      setChatMessages(Array.isArray(data) ? data : []);
    } catch (err) {
      setErrorMessage(err.message || "Something went wrong");
    }
  }, [cartId]);

  useEffect(() => {
    if (!cartId) return;
    setLoading(true);
    fetchProducts().finally(() => setLoading(false));
  }, [cartId, fetchProducts]);

  useEffect(() => {
    if (cartId) fetchMessages();
  }, [cartId, fetchMessages]);

  useEffect(() => {
    if (cartInfo || !cartId || !userId) return;

    const fetchCartInfo = async () => {
      try {
        const carts = await apiFetch("/carts");
        const match = carts.find(
          (c) => String(c.cart_id) === String(cartId)
        );
        if (!match) {
          setErrorMessage("Cart not found");
          return;
        }
        setCartInfo({
          cartName: match.cart_name,
          cartDesc: match.cart_description,
          cartPrice: match.total,
          isShared: match.is_shared,
        });
      } catch (err) {
        setErrorMessage(err.message || "Something went wrong");
      }
    };

    fetchCartInfo();
  }, [cartInfo, cartId, userId]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const data = await apiFetch(`/carts/${cartId}/users`);
        setUsers(data);
      } catch (err) {
        setErrorMessage(
          err.message || "Something went wrong while fetching users"
        );
      }
    };

    if (cartId) {
      fetchUsers();
    }
  }, [cartId]);

  //Increase/Decrease quantity------------------------------------

  const handleIncreaseQuantity = async (cartIdOfItem, cartItemId) => {
    try {
      const data = await apiFetch(`/cart-items/${cartItemId}/increase`, {
        method: "PATCH",
      });

      setCartItems((prev) =>
        prev.map((item) =>
          item.cart_item_id === cartItemId
            ? { ...item, quantity: data.new_quantity }
            : item
        )
      );

      setTotalCost(data.cart_total);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  const handleDecreaseQuantity = async (cartIdOfItem, cartItemId) => {
    try {
      const data = await apiFetch(`/cart-items/${cartItemId}/decrease`, {
        method: "PATCH",
      });

      if (data.new_quantity === undefined) {
        // The backend deletes the row when the quantity would drop below 1.
        setCartItems((prev) =>
          prev.filter((item) => item.cart_item_id !== cartItemId)
        );
      } else {
        setCartItems((prev) =>
          prev.map((item) =>
            item.cart_item_id === cartItemId
              ? { ...item, quantity: data.new_quantity }
              : item
          )
        );
      }

      setTotalCost(data.cart_total);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  //Approve or Reject product -------------------------------------

  const handleApproveProduct = async (cartIdOfItem, cartItemId) => {
    try {
      const data = await apiFetch(`/cart-items/${cartItemId}/approve`, {
        method: "PATCH",
      });

      setCartItems((prev) =>
        prev.map((item) =>
          item.cart_item_id === cartItemId ? { ...item, approved: true } : item
        )
      );

      setTotalCost(data.cart_total);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  const handleRejectProduct = async (cartIdOfItem, cartItemId) => {
    try {
      const data = await apiFetch(`/cart-items/${cartItemId}`, {
        method: "DELETE",
      });

      // Disapproving removes the item from the cart.
      setCartItems((prev) =>
        prev.filter((item) => item.cart_item_id !== cartItemId)
      );

      setTotalCost(data.cart_total);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  const handleChatSubmit = async () => {
    const text = chatMessage.trim();
    if (text === "" || isSending) return;

    const optimisticMessage = {
      message_id: `pending-${Date.now()}`,
      cart_id: Number(cartId),
      sender_id: Number(userId),
      sender_type: "user",
      sender_name: userName,
      message_content: text,
    };

    setChatMessages((prev) => [...prev, optimisticMessage]);
    setChatMessage("");
    setIsSending(true);

    try {
      // The sender is taken from the bearer token, not sent in the body.
      const reply = await apiFetch("/messages/ask", {
        method: "POST",
        body: JSON.stringify({
          cart_id: Number(cartId),
          message: text,
        }),
      });

      // Re-read the thread so ids and timestamps come from the server.
      await fetchMessages();

      // cart_changed also covers quantity edits and removals, not just adds.
      if (reply.cart_changed || reply.items_added > 0) {
        await fetchProducts();
      }
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
      // The message was stored server-side even if the reply failed, so
      // re-read the thread instead of guessing what survived.
      await fetchMessages();
    } finally {
      setIsSending(false);
    }
  };

  return (
    <>
      <ErrorPopup message={errorMessage} onClose={() => setErrorMessage("")} />
      <div className="selected-cart-default select-cart-body">

        {loading ? (
          <div className="loader"></div>
        ) : (
          <div className="selected-cart-default select-cart-body-content">
            <div className="selected-cart-default left-div">
              <div className="selected-cart-default left-header">
                {cartName}
                <span>{cartDesc}</span>
              </div>
              <div className="selected-cart-default products-div">
                <div className="selected-cart-default products-div">
                  {cartItems.length === 0 ? (
                    <div className="no-items-message">
                      No items in this cart.
                    </div>
                  ) : (
                    cartItems.map((p) => (
                      <Product
                        key={p.cart_item_id}
                        pId={p.cart_item_id}
                        name={p.product.product_name}
                        desc={p.product.product_description}
                        cost={p.product.price}
                        createdBy={p.added_by}
                        quantity={p.quantity}
                        approved={p.approved}
                        img={p.product.image_url}
                        cartId={p.cart_id}
                        onIncrease={handleIncreaseQuantity}
                        onDecrease={handleDecreaseQuantity}
                        onApprove={handleApproveProduct}
                        onReject={handleRejectProduct}
                        createdByName={
                          users.find((u) => u.user_id === p.added_by)
                            ?.user_name || "Unknown User"
                        }
                      />
                    ))
                  )}
                </div>
              </div>
              <div className="selected-cart-default left-footer">
                <div className="left-footer-total">
                  <span className="left-footer-text">
                    Total (approved items)
                  </span>
                  <span className="left-footer-price">
                    ${totalCost !== null ? totalCost : cartPrice ?? "0.00"}
                  </span>
                </div>
                <button
                  type="button"
                  className="left-footer-checkout"
                  disabled={!cartItems.some((item) => item.approved)}
                  title={
                    cartItems.some((item) => item.approved)
                      ? "Buy the approved items in this cart"
                      : "Approve at least one item to check out"
                  }
                  onClick={() => navigate(`/checkout?cart=${cartId}`)}
                >
                  Proceed to checkout
                </button>
              </div>
            </div>
            <div className="selected-cart-default right-div">
              <div className="selected-cart-default chatbot">
                <div className="selected-cart-default right-header">
                  Your Shopping Assistant
                </div>
                <div className="selected-cart-default right-body">
                  {chatMessages.length === 0 ? (
                    <div className="no-items-message">
                      No messages yet. Ask the assistant for something.
                    </div>
                  ) : (
                    chatMessages.map((chat) => (
                      <Chats
                        key={chat.message_id}
                        chat={chat.message_content}
                        user={
                          chat.sender_name ||
                          (chat.sender_type === "assistant"
                            ? "Assistant"
                            : "User")
                        }
                        sendType={chat.sender_type}
                        senderId={chat.sender_id}
                      />
                    ))
                  )}
                </div>
                <div className="selected-cart-default right-chat-field">
                  <textarea
                    placeholder="Type a message..."
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                  ></textarea>
                  <button
                    type="button"
                    className="selected-cart-default chat-submit"
                    onClick={handleChatSubmit}
                    disabled={isSending}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      fill="currentColor"
                      className="bi bi-arrow-up"
                      viewBox="0 0 16 16"
                    >
                      <path
                        fillRule="evenodd"
                        d="M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {isShared ? (
                <div className="selected-cart-default display-users-div">
                  {users.map((user) => (
                    <div
                      className="selected-cart-default user-div"
                      key={user.user_id}
                    >
                      <div className="selected-cart-default user-img-div">
                        <img
                          src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
                            user.user_name
                          )}`}
                          alt={user.user_name}
                          className="user-avatar"
                        />
                      </div>
                      <div className="selected-cart-default user-name">
                        {user.user_name}
                      </div>
                    </div>
                  ))}
                </div>
              ) : null}
            </div>
          </div>
        )}

        <div className="selected-cart-default select-cart-footer"></div>
      </div>
    </>
  );
}
