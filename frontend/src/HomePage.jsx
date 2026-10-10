import "./HomePage.css";
import Cart from "./Cart";
import { useEffect, useState } from "react";
import CartPopup from "./CartPopup";
import ErrorPopup from "./Error";
import { apiFetch } from "./api";

export default function HomePage(props) {
  const userId = localStorage.getItem("userId");
  const [cartData, setCartData] = useState([]);
  const [showPopup, setShowPopup] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  //To fetch all carts------------------------UPDATE

  useEffect(() => {
    const fetchCarts = async () => {
      setIsLoading(true);
      try {
        // The backend derives the owner from the token; no id in the path.
        const data = await apiFetch("/carts");
        setCartData(Array.isArray(data) ? data : []);
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
      await apiFetch(`/carts/${cartId}`, { method: "DELETE" });
      setCartData((prevCarts) =>
        prevCarts.filter((cart) => cart.cart_id !== cartId)
      );
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    }
  };

  //To add a new cart

  const handleAddCart = async (newCart) => {
    setIsLoading(true);
    try {
      const savedCart = await apiFetch("/carts", {
        method: "POST",
        body: JSON.stringify(newCart),
      });

      setCartData((prev) => [...prev, savedCart]);
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <>
      <ErrorPopup message={errorMessage} onClose={() => setErrorMessage("")} />
      <div className="default-home homepage-body">
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
            <div className="loader"></div>
          ) : (
            cartData.map((cart) => (
              <Cart
                key={cart.cart_id}
                cartId={cart.cart_id}
                cartName={cart.cart_name}
                cartDesc={cart.cart_description}
                date={cart.date_created}
                price={cart.total}
                onDelete={() => handleDelete(cart.cart_id)}
                shared={cart.is_shared}
              />
            ))
          )}
        </div>
        <div className="default-home footer"></div>
      </div>
    </>
  );
}
