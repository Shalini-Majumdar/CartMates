import "./SelectedCart.css";
import Product from "./Product";
import { useState, useEffect } from "react";
import { useParams, useLocation } from "react-router-dom";
import Error from "./Error";
import Chats from "./Chats";

export default function SelectedCart(props) {
  const userId = localStorage.getItem("userId");
  const userName = localStorage.getItem("userName");
  const location = useLocation();
  const { cartId } = useParams();
  const [cartItems, setCartItems] = useState([]);
  const { cartName, cartPrice, isShared, cartDesc } =
    location.state || "no data";
  const [loading, setLoading] = useState(true);
  const [chatMessage, setChatMessage] = useState("");
  const [chatMessages, setChatMessages] = useState([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [users, setUsers] = useState([]);
  const [totalCost, setTotalCost] = useState(0);

  // const users = [
  //   { id: 1, name: "Alice Sharma" },
  //   { id: 2, name: "Bob Kumar" },
  //   { id: 3, name: "Charlie D'Souza" },
  //   { id: 4, name: "Diana Mehta" },
  //   { id: 5, name: "Ethan Reddy" },
  // ];

  const sampleChats = [
    {
      id: 1,
      sender: "Alice Sharma",
      senderType: "user",
      message: "Hey team, should we add apples to the cart?",
      sender_id: 8,
    },
    {
      id: 2,
      sender: "Bob Kumar",
      senderType: "user",
      message: "Yes, and maybe some bananas too.",
      sender_id: 2,
    },
    {
      id: 3,
      sender: "Charlie D'Souza",
      senderType: "user",
      message: "Don't forget about the milk!",

      sender_id: 3,
    },
    {
      id: 4,
      sender: "CartBot",
      senderType: "bot",
      message: "Ive added apples, bananas, and milk to the cart for you.",
      sender_id: 0,
    },
    {
      id: 5,
      sender: "Alice Sharma",
      senderType: "user",
      message: "Hey team, should we add apples to the cart?",
      sender_id: 8,
    },
    {
      id: 6,
      sender: "Bob Kumar",
      senderType: "user",
      message: "Yes, and maybe some bananas too.",
      sender_id: 2,
    },
    {
      id: 7,
      sender: "Charlie D'Souza",
      senderType: "user",
      message: "Don't forget about the milk!",
      sender_id: 3,
    },
    {
      id: 8,
      sender: "CartBot",
      senderType: "bot",
      message: "Ive added apples, bananas, and milk to the cart for you.",
      sender_id: 0,
    },
  ];

  console.log(location.state);
  //To fetch all products for the selected cart------------------

  useEffect(() => {
    setLoading(true);
    const fetchProducts = async () => {
      setLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/products/${cartId}`);
        const data = await res.json();
        setCartItems(data);
      } catch (err) {
        setErrorMessage(err.message || "Something went wrong");
        setCartItems([]);
      } finally {
        setLoading(false);
      }
    };

    fetchProducts();
  }, [cartId]);

  //Increase/Decrease quantity------------------------------------

  const handleIncreaseQuantity = async (cartId, itemId) => {
    try {
      const res = await fetch(
        `http://localhost:8000/products/${itemId}/increase`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cart_item_id: cartId }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to increase quantity");
      }

      setCartItems((prev) =>
        prev.map((item) =>
          item.pId === itemId ? { ...item, quantity: item.quantity + 1 } : item
        )
      );

      setTotalCost(res.updatedTotalCost);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  const handleDecreaseQuantity = async (cartId, itemId) => {
    try {
      const res = await fetch(
        `http://localhost:8000/products/${itemId}/decrease`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ cart__item_id: cartId }),
        }
      );

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.detail || "Failed to decrease quantity");
      }

      setCartItems((prev) =>
        prev.map((item) =>
          item.pId === itemId ? { ...item, quantity: item.quantity - 1 } : item
        )
      );

      setTotalCost(res.updatedTotalCost);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  //Approve or Reject product -------------------------------------

  const handleApproveProduct = async (cartId, itemId) => {
    try {
      await fetch(`http://localhost:8000/products/${itemId}/approve`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cart_item_id: cartId }),
      });

      setCartItems((prev) =>
        prev.map((item) =>
          item.cart_item_id === itemId ? { ...item, approved: true } : item
        )
      );
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  const handleRejectProduct = async (cartId, itemId) => {
    try {
      await fetch(`http://localhost:8000/products/${itemId}/reject`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cart_item_id: cartId }),
      });

      setCartItems((prev) =>
        prev.map((item) =>
          item.cart_item_id === itemId ? { ...item, approved: false } : item
        )
      );
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  const handleChatSubmit = async () => {
    if (chatMessage.trim() === "") return;

    const newUserMessage = {
      sender_id: userId,
      cart_id: cartId,
      message: chatMessage,
      //add username
    };

    setChatMessages((prev) => [...prev, newUserMessage]);
    setChatMessage("");

    try {
      const res = await fetch("http://localhost:5000/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: newUserMessage.message,
          cart_id: cartId,
        }),
      });

      const reply = await res.json();
      console.log("Assistant reply:", reply);

      const botMessage = {
        id: reply.id,
        sender: reply.sender,
        message: reply.message || "Bot replied",
        sender_id: 0,
      };

      setChatMessages((prev) => [...prev, botMessage]);

      if (reply.products) {
        setCartItems((prevItems) => [...prevItems, ...reply.products]);
      }
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  useEffect(() => {
    const fetchMessages = async () => {
      try {
        const res = await fetch(`http://localhost:8000/messages/${cartId}`);

        if (!res.ok) {
          setErrorMessage("Failed to fetch messages");
        }

        const data = await res.json();
        setChatMessages(data);
      } catch (err) {
        setErrorMessage(err.message || "Something went wrong");
      }
    };
    if (cartId) {
      fetchMessages();
    }
  }, [cartId]);

  useEffect(() => {
    const fetchUsers = async () => {
      try {
        const res = await fetch(`http://localhost:8000/carts/${cartId}/users`);
        if (!res.ok) throw new Error("Failed to fetch cart users");
        const data = await res.json();
        setUsers(data); // Populate users array with API response
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

  return (
    <>
      <div className="selected-cart-default select-cart-body">
        <div className="selected-cart-default select-cart-header"></div>

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
                        key={`${p.cart_item_id}-${p.approved}`}
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
                <span className="left-footer-text">Price</span>
                <span className="left-footer-price">
                  ${totalCost ? totalCost : cartPrice}
                </span>
              </div>
            </div>
            <div className="selected-cart-default right-div">
              <div className="selected-cart-default chatbot">
                <div className="selected-cart-default right-header">
                  Your Shopping Assistant
                </div>
                {/* change sampleChats */}
                <div className="selected-cart-default right-body">
                  {sampleChats.map((chat) => (
                    <Chats
                      key={chat.id}
                      chat={chat.message}
                      user={chat.sender}
                      sendType={chat.senderType}
                      senderId={chat.sender_id}
                    />
                  ))}
                </div>
                <div className="selected-cart-default right-chat-field">
                  <textarea
                    placeholder="Type a message..."
                    value={chatMessage}
                    onChange={(e) => setChatMessage(e.target.value)}
                  ></textarea>
                  <button
                    type="submit"
                    className="selected-cart-default chat-submit"
                    onClick={handleChatSubmit}
                  >
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      fill="currentColor"
                      class="bi bi-arrow-up"
                      viewBox="0 0 16 16"
                    >
                      <path
                        fill-rule="evenodd"
                        d="M8 15a.5.5 0 0 0 .5-.5V2.707l3.146 3.147a.5.5 0 0 0 .708-.708l-4-4a.5.5 0 0 0-.708 0l-4 4a.5.5 0 1 0 .708.708L7.5 2.707V14.5a.5.5 0 0 0 .5.5"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {isShared ? (
                <>
                  <div className="selected-cart-default display-users-div">
                    {users.map((user) => (
                      <div
                        className="selected-cart-default user-div"
                        key={user.id}
                      >
                        <div className="selected-cart-default user-img-div">
                          <img
                            src={`https://api.dicebear.com/7.x/initials/svg?seed=${user.user_name}`}
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
                </>
              ) : (
                <></>
              )}
            </div>
          </div>
        )}

        <div className="selected-cart-default select-cart-footer"></div>
      </div>
    </>
  );
}
