import "./HomePage.css";
import Cart from "./Cart";
import { Link, useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import CartPopup from "./CartPopup";

export default function HomePage(props) {
  const userId = localStorage.getItem("userId");
  const userName = localStorage.getItem("userName");
  const [cartData, setCartData] = useState([]);
  const [showPopup, setShowPopup] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const navigate = useNavigate();

  //To fetch all carts------------------------UPDATE

  useEffect(() => {
    console.log("Updated cartData:", cartData);
  }, [cartData]);

  useEffect(() => {
    const fetchCarts = async () => {
      setIsLoading(true);
      try {
        const res = await fetch(`http://localhost:8000/carts/${userId}`);
        const data = await res.json();
        setCartData(data);
      } catch (error) {
        setErrorMessage(error.message || "Something went wrong");
        setCartData([]);
      } finally {
        setIsLoading(false);
      }
    };

    if (userId) {
      fetchCarts();
    }
  }, [userId]);

  //To delete a cart-------------------------

  const handleDelete = async (cartId) => {
    try {
      const res = await fetch(`http://localhost:8000/carts/${cartId}`, {
        method: "DELETE",
      });

      if (res.ok) {
        setCartData((prevCarts) =>
          prevCarts.filter((cart) => cart.cart_id !== cartId)
        );
        console.log("Cart deleted successfully");
      } else {
        setErrorMessage("Something went wrong");
      }
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  //To add a new cart

  const handleAddCart = async (newCart) => {
    setIsLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/carts/${userId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newCart),
      });

      if (!res.ok) {
        throw new Error("Failed to add cart");
      }

      const savedCart = await res.json();

      const updatedCart = {
        cart_id: savedCart.cart_id,
        cart_name: savedCart.cart_name,
        cart_description: savedCart.cart_description,
        date_created: savedCart.date_created,
        total: savedCart.total,
        // approved: savedCart.approved,
        people: savedCart.people,
        is_shared: savedCart.is_shared,
      };

      setCartData((prev) => [...prev, updatedCart]);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <div className="default-home homepage-body">
        <div className="default-home header">Welcome, {userName}</div>
        <div className="default-home main-heading-div">
          <div className="default-home main-title">
            Your Carts
            <span className="subtitle">
              Manage and organize your shopping collections
            </span>
          </div>
          <div className="default-home main-button-div">
            <button
              className="default-home main-button"
              onClick={() => setShowPopup(true)}
            >
              New Cart
            </button>
          </div>

          {showPopup && (
            <CartPopup
              onSubmit={handleAddCart}
              onClose={() => setShowPopup(false)}
            />
          )}
        </div>
        <div className="default-home main-body">
          {isLoading ? (
            // <div className="loading-popup">Loading carts...</div>
            <div class="loader"></div>
          ) : (
            cartData.map((cart) => (
              <Cart
                key={cart.cart_id}
                cartId={cart.cart_id}
                cartName={cart.cart_name}
                cartDesc={cart.cart_description}
                people={cart.people}
                date={cart.date_created}
                price={cart.total}
                onDelete={() => handleDelete(cart.cart_id)}
                shared={cart.is_shared}
              />
            ))
          )}
        </div>
        <div className="default-home footer">
          <Link
            to="/selectedcart"
            className="default-login login-button"
          ></Link>
        </div>
      </div>
    </>
  );
}
