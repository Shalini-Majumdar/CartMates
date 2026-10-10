import "./NavBar.css";
import { useEffect, useState } from "react";
import {
  Link,
  NavLink,
  useLocation,
  useNavigate,
  useSearchParams,
} from "react-router-dom";
import { clearSession } from "./api";

export default function NavBar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const userName = localStorage.getItem("userName") || "";
  const [query, setQuery] = useState("");

  // What the box searches depends on the page: the cart list, the items in
  // the open cart, or (everywhere else) the store's products.
  const scope =
    location.pathname === "/carts"
      ? "carts"
      : location.pathname.startsWith("/cart/")
      ? "cart-items"
      : "products";
  const placeholder = {
    carts: "Search your carts…",
    "cart-items": "Search this cart…",
    products: "Search products…",
  }[scope];
  const filtersInPlace = scope !== "products";

  // Keep the box in step with the page's ?q= (the shop's, or the filter of
  // the carts / cart page) as you move between pages.
  useEffect(() => {
    setQuery(
      location.pathname === "/home" || filtersInPlace
        ? searchParams.get("q") || ""
        : ""
    );
  }, [location.pathname, searchParams, filtersInPlace]);

  const handleChange = (e) => {
    const value = e.target.value;
    setQuery(value);
    // Carts and cart items filter as you type, without adding history entries.
    if (filtersInPlace) {
      setSearchParams(value.trim() ? { q: value } : {}, { replace: true });
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (filtersInPlace) return;
    const q = query.trim();
    navigate(q ? `/home?q=${encodeURIComponent(q)}` : "/home");
  };

  const handleLogout = () => {
    clearSession();
    navigate("/", { replace: true });
  };

  const linkClass = ({ isActive }) =>
    isActive ? "navbar-link active" : "navbar-link";

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <div className="navbar-left">
          <Link to="/home" className="navbar-brand">
            <span className="navbar-logo" aria-hidden="true">
              <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
                <path d="M7 18a2 2 0 1 0 0 4 2 2 0 0 0 0-4Zm10 0a2 2 0 1 0 0 4 2 2 0 0 0 0-4ZM5.2 4l.4 2H20a1 1 0 0 1 1 1.2l-1.4 7A2 2 0 0 1 17.6 16H8a2 2 0 0 1-2-1.6L3.6 3H2a1 1 0 0 1 0-2h2.4a1 1 0 0 1 1 .8Z" />
              </svg>
            </span>
            <span className="navbar-brand-text">CartMates</span>
          </Link>
          <nav className="navbar-links">
            <NavLink to="/home" className={linkClass}>
              Home
            </NavLink>
            <NavLink to="/carts" className={linkClass}>
              My Carts
            </NavLink>
          </nav>
        </div>

        <form className="navbar-search" onSubmit={handleSearch} role="search">
          <svg
            className="navbar-search-icon"
            viewBox="0 0 16 16"
            width="15"
            height="15"
            fill="currentColor"
            aria-hidden="true"
          >
            <path d="M11.7 10.3a6.5 6.5 0 1 0-1.4 1.4l3.5 3.5a1 1 0 0 0 1.4-1.4l-3.5-3.5ZM6.5 11a4.5 4.5 0 1 1 0-9 4.5 4.5 0 0 1 0 9Z" />
          </svg>
          <input
            type="search"
            placeholder={placeholder}
            aria-label={placeholder.replace("…", "")}
            value={query}
            onChange={handleChange}
          />
        </form>

        <div className="navbar-right">
          <NavLink to="/checkout" className="navbar-checkout">
            <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">
              <path d="M0 4a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2v1H0V4Zm0 3h16v5a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V7Zm3 3a1 1 0 0 0 0 2h2a1 1 0 0 0 0-2H3Z" />
            </svg>
            <span>Checkout</span>
          </NavLink>
          <div className="navbar-user" title={userName}>
            <img
              src={`https://api.dicebear.com/7.x/initials/svg?seed=${encodeURIComponent(
                userName
              )}`}
              alt=""
            />
            <span className="navbar-user-name">{userName}</span>
          </div>
          <button type="button" className="navbar-logout" onClick={handleLogout}>
            <svg viewBox="0 0 16 16" width="15" height="15" fill="currentColor" aria-hidden="true">
              <path d="M6 2a1 1 0 0 1 0 2H3v8h3a1 1 0 1 1 0 2H2a1 1 0 0 1-1-1V3a1 1 0 0 1 1-1h4Zm4.3 2.3a1 1 0 0 1 1.4 0l3 3a1 1 0 0 1 0 1.4l-3 3a1 1 0 0 1-1.4-1.4L11.6 9H6a1 1 0 0 1 0-2h5.6l-1.3-1.3a1 1 0 0 1 0-1.4Z" />
            </svg>
            <span>Logout</span>
          </button>
        </div>
      </div>
    </header>
  );
}
