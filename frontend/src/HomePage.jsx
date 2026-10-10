import "./HomePage.css";
import Cart from "./Cart";
import { useEffect, useState } from "react";
import CartPopup from "./CartPopup";
import ErrorPopup from "./Error";
import { apiFetch } from "./api";
import { useSearchParams } from "react-router-dom";

export default function HomePage(props) {
  const userId = localStorage.getItem("userId");
  const [cartData, setCartData] = useState([]);
  const [showPopup, setShowPopup] = useState(false);
  const [editingCart, setEditingCart] = useState(null);
  // Set by the search box in the top bar.
  const [searchParams] = useSearchParams();
  const search = (searchParams.get("q") || "").trim().toLowerCase();
  const visibleCarts = search
    ? cartData.filter(
        (cart) =>
          cart.cart_name.toLowerCase().includes(search) ||
          (cart.cart_description || "").toLowerCase().includes(search)
      )
    : cartData;
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

  //To edit a cart's name, description or members

  const handleEditCart = async (cartId, changes) => {
    try {
      const updated = await apiFetch(`/carts/${cartId}`, {
        method: "PATCH",
        body: JSON.stringify(changes),
      });
      setCartData((prev) =>
        prev.map((cart) => (cart.cart_id === cartId ? updated : cart))
      );
    } catch (error) {
      setErrorMessage(error.message || "Something went wrong");
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

          {editingCart && (
            <CartPopup
              cart={editingCart}
              onSubmit={(changes) => handleEditCart(editingCart.cart_id, changes)}
              onClose={() => setEditingCart(null)}
            />
          )}
        </div>
        <div className="default-home main-body">
          {isLoading ? (
            // <div className="loading-popup">Loading carts...</div>
            <div className="loader"></div>
          ) : search && visibleCarts.length === 0 ? (
            <div className="no-carts-message">
              No carts match “{searchParams.get("q")}”.
            </div>
          ) : (
            visibleCarts.map((cart) => (
              <Cart
                key={cart.cart_id}
                cartId={cart.cart_id}
                cartName={cart.cart_name}
                cartDesc={cart.cart_description}
                date={cart.date_created}
                price={cart.total}
                onDelete={() => handleDelete(cart.cart_id)}
                // Only the creator may edit, matching the backend rule.
                onEdit={
                  String(cart.created_by) === String(userId)
                    ? () => setEditingCart(cart)
                    : undefined
                }
                membersKey={(cart.shared_usernames || []).join(",")}
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
