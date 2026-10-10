import "./ShopPage.css";
import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import ErrorPopup from "./Error";
import { apiFetch } from "./api";
import { money } from "./format";

const PLACEHOLDER_IMG =
  "https://www.svgrepo.com/show/508699/landscape-placeholder.svg";
const LAST_CART_KEY = "lastCartId";

const SORT_OPTIONS = [
  { value: "name", label: "Name (A–Z)" },
  { value: "price_asc", label: "Price: low to high" },
  { value: "price_desc", label: "Price: high to low" },
  { value: "newest", label: "Newest" },
];

const PRICE_PRESETS = [
  { label: "Under ₹250", min: "", max: "250" },
  { label: "₹250 – ₹500", min: "250", max: "500" },
  { label: "₹500 – ₹900", min: "500", max: "900" },
  { label: "Over ₹900", min: "900", max: "" },
];

function readLastCart() {
  try {
    return localStorage.getItem(LAST_CART_KEY);
  } catch {
    return null;
  }
}

function writeLastCart(cartId) {
  try {
    localStorage.setItem(LAST_CART_KEY, String(cartId));
  } catch {
    // Remembering the cart is a convenience only.
  }
}

export default function ShopPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const search = searchParams.get("q") || "";

  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [category, setCategory] = useState("");
  const [minPrice, setMinPrice] = useState("");
  const [maxPrice, setMaxPrice] = useState("");
  const [sort, setSort] = useState("name");
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    apiFetch("/products/categories")
      .then((data) => setCategories(Array.isArray(data) ? data : []))
      .catch((err) => setErrorMessage(err.message || "Could not load categories"));
  }, []);

  // Debounced so typing a price does not fire a request per keystroke.
  useEffect(() => {
    const params = new URLSearchParams({ sort });
    if (search) params.set("search", search);
    if (category) params.set("category", category);
    if (minPrice !== "") params.set("min_price", minPrice);
    if (maxPrice !== "") params.set("max_price", maxPrice);

    let cancelled = false;
    const timer = setTimeout(async () => {
      setIsLoading(true);
      try {
        const data = await apiFetch(`/products?${params}`);
        if (!cancelled) setProducts(Array.isArray(data) ? data : []);
      } catch (err) {
        if (!cancelled) setErrorMessage(err.message || "Could not load products");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }, 250);

    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [search, category, minPrice, maxPrice, sort]);

  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(timer);
  }, [toast]);

  const hasFilters = Boolean(search || category || minPrice || maxPrice);

  const clearFilters = () => {
    setCategory("");
    setMinPrice("");
    setMaxPrice("");
    setSearchParams({});
  };

  const activePreset = PRICE_PRESETS.find(
    (p) => p.min === minPrice && p.max === maxPrice
  );

  return (
    <>
      <ErrorPopup message={errorMessage} onClose={() => setErrorMessage("")} />

      <div className="shop-page">
        <section className="shop-hero">
          <div>
            <h1>Shop for your group</h1>
            <p>
              Browse the store, add items to any of your carts, or ask a cart's
              assistant to pick for you.
            </p>
          </div>
        </section>

        <div className="shop-layout">
          <aside className="shop-filters" aria-label="Filters">
            <div className="shop-filters-header">
              <h2>Filters</h2>
              {hasFilters && (
                <button type="button" className="ui-link" onClick={clearFilters}>
                  Clear all
                </button>
              )}
            </div>

            <div className="filter-group filter-group-category">
              <h3>Category</h3>
              <button
                type="button"
                className={`filter-option ${category === "" ? "active" : ""}`}
                onClick={() => setCategory("")}
              >
                All products
              </button>
              {categories.map((c) => (
                <button
                  type="button"
                  key={c}
                  className={`filter-option ${category === c ? "active" : ""}`}
                  onClick={() => setCategory(c)}
                >
                  {c}
                </button>
              ))}
            </div>

            <div className="filter-group">
              <h3>Price</h3>
              <div className="price-presets">
                {PRICE_PRESETS.map((p) => (
                  <button
                    type="button"
                    key={p.label}
                    className={`ui-chip ${activePreset === p ? "active" : ""}`}
                    onClick={() => {
                      if (activePreset === p) {
                        setMinPrice("");
                        setMaxPrice("");
                      } else {
                        setMinPrice(p.min);
                        setMaxPrice(p.max);
                      }
                    }}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
              <div className="price-range">
                <label>
                  <span>Min ₹</span>
                  <input
                    type="number"
                    min="0"
                    step="10"
                    inputMode="decimal"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                  />
                </label>
                <span className="price-range-dash">–</span>
                <label>
                  <span>Max ₹</span>
                  <input
                    type="number"
                    min="0"
                    step="10"
                    inputMode="decimal"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                  />
                </label>
              </div>
            </div>
          </aside>

          <main className="shop-results">
            <div className="shop-results-bar">
              <div className="shop-results-count">
                {isLoading ? (
                  "Loading products…"
                ) : (
                  <>
                    <strong>{products.length}</strong>{" "}
                    {products.length === 1 ? "product" : "products"}
                    {search && (
                      <>
                        {" "}
                        for “{search}”{" "}
                        <button
                          type="button"
                          className="ui-link"
                          onClick={() => setSearchParams({})}
                        >
                          clear search
                        </button>
                      </>
                    )}
                  </>
                )}
              </div>
              <label className="shop-sort">
                <span>Sort by</span>
                <select value={sort} onChange={(e) => setSort(e.target.value)}>
                  {SORT_OPTIONS.map((o) => (
                    <option key={o.value} value={o.value}>
                      {o.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            {!isLoading && products.length === 0 ? (
              <div className="shop-empty">
                <h3>No products match these filters</h3>
                <p>Try a different search, category or price range.</p>
                {hasFilters && (
                  <button type="button" className="ui-btn-primary" onClick={clearFilters}>
                    Clear filters
                  </button>
                )}
              </div>
            ) : (
              <div className={`product-grid ${isLoading ? "is-loading" : ""}`}>
                {products.map((p) => (
                  <article className="shop-card" key={p.product_id}>
                    <div className="shop-card-img">
                      <img
                        src={p.image_url || PLACEHOLDER_IMG}
                        alt=""
                        loading="lazy"
                        onError={(e) => {
                          e.currentTarget.onerror = null;
                          e.currentTarget.src = PLACEHOLDER_IMG;
                        }}
                      />
                    </div>
                    <div className="shop-card-body">
                      {p.category && (
                        <span className="shop-card-category">{p.category}</span>
                      )}
                      <h3 className="shop-card-name">{p.product_name}</h3>
                      <p className="shop-card-desc">{p.product_description}</p>
                      <div className="shop-card-footer">
                        <span className="shop-card-price">{money(p.price)}</span>
                        <button
                          type="button"
                          className="ui-btn-primary ui-btn-small"
                          onClick={() => setSelectedProduct(p)}
                        >
                          Add to cart
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
            <p className="shop-credits">
              Product photos via{" "}
              <a href="https://openverse.org" target="_blank" rel="noreferrer">
                Openverse
              </a>{" "}
              (CC0, public domain and CC BY).{" "}
              <a href="/products/CREDITS.md" target="_blank" rel="noreferrer">
                Photo credits
              </a>
            </p>
          </main>
        </div>
      </div>

      {selectedProduct && (
        <AddToCartDialog
          product={selectedProduct}
          onClose={() => setSelectedProduct(null)}
          onAdded={(result) => {
            setSelectedProduct(null);
            setToast(result);
          }}
          onError={setErrorMessage}
        />
      )}

      {toast && (
        <div className="shop-toast" role="status">
          <span>
            Added {toast.quantity} × {toast.productName} to{" "}
            <strong>{toast.cartName}</strong>
          </span>
          <Link to={`/cart/${toast.cartId}`}>View cart</Link>
          <button type="button" aria-label="Dismiss" onClick={() => setToast(null)}>
            ×
          </button>
        </div>
      )}
    </>
  );
}

function AddToCartDialog({ product, onClose, onAdded, onError }) {
  const [carts, setCarts] = useState(null);
  const [cartId, setCartId] = useState("");
  const [newCartName, setNewCartName] = useState("");
  const [quantity, setQuantity] = useState(1);
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    apiFetch("/carts")
      .then((data) => {
        const list = Array.isArray(data) ? data : [];
        setCarts(list);
        const last = readLastCart();
        const preferred = list.find((c) => String(c.cart_id) === last) || list[0];
        setCartId(preferred ? String(preferred.cart_id) : "new");
      })
      .catch((err) => {
        onError(err.message || "Could not load your carts");
        onClose();
      });
    // Load once per opening; the callbacks are new on every parent render.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const onKey = (e) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  const lineTotal = useMemo(
    () => Number(product.price) * quantity,
    [product.price, quantity]
  );

  const canSubmit =
    !isSaving &&
    carts !== null &&
    (cartId === "new" ? newCartName.trim() !== "" : cartId !== "");

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    setIsSaving(true);
    try {
      let target;
      if (cartId === "new") {
        target = await apiFetch("/carts", {
          method: "POST",
          body: JSON.stringify({
            cart_name: newCartName.trim(),
            cart_description: "",
            is_shared: false,
            shared_with: [],
          }),
        });
      } else {
        target = carts.find((c) => String(c.cart_id) === cartId);
      }

      await apiFetch(`/carts/${target.cart_id}/items`, {
        method: "POST",
        body: JSON.stringify({ product_id: product.product_id, quantity }),
      });
      writeLastCart(target.cart_id);
      onAdded({
        cartId: target.cart_id,
        cartName: target.cart_name,
        productName: product.product_name,
        quantity,
      });
    } catch (err) {
      onError(err.message || "Could not add the item");
      setIsSaving(false);
    }
  };

  return (
    <div className="dialog-overlay" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <form
        className="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="add-to-cart-title"
        onSubmit={handleSubmit}
      >
        <div className="dialog-header">
          <h2 id="add-to-cart-title">Add to cart</h2>
          <button type="button" className="dialog-close" aria-label="Close" onClick={onClose}>
            ×
          </button>
        </div>

        <div className="dialog-product">
          <img
            src={product.image_url || PLACEHOLDER_IMG}
            alt=""
            onError={(e) => {
              e.currentTarget.onerror = null;
              e.currentTarget.src = PLACEHOLDER_IMG;
            }}
          />
          <div>
            <div className="dialog-product-name">{product.product_name}</div>
            <div className="dialog-product-price">{money(product.price)} each</div>
          </div>
        </div>

        <div className="dialog-field">
          <span className="dialog-label">Quantity</span>
          <div className="qty-stepper">
            <button
              type="button"
              aria-label="Decrease quantity"
              disabled={quantity <= 1}
              onClick={() => setQuantity((q) => Math.max(1, q - 1))}
            >
              −
            </button>
            <span aria-live="polite">{quantity}</span>
            <button
              type="button"
              aria-label="Increase quantity"
              disabled={quantity >= 99}
              onClick={() => setQuantity((q) => Math.min(99, q + 1))}
            >
              +
            </button>
          </div>
        </div>

        <div className="dialog-field">
          <span className="dialog-label">Which cart?</span>
          {carts === null ? (
            <div className="dialog-muted">Loading your carts…</div>
          ) : (
            <div className="cart-choices">
              {carts.map((c) => (
                <label
                  key={c.cart_id}
                  className={`cart-choice ${cartId === String(c.cart_id) ? "active" : ""}`}
                >
                  <input
                    type="radio"
                    name="cart"
                    value={c.cart_id}
                    checked={cartId === String(c.cart_id)}
                    onChange={(e) => setCartId(e.target.value)}
                  />
                  <span className="cart-choice-name">{c.cart_name}</span>
                  {c.is_shared && <span className="ui-tag">Shared</span>}
                </label>
              ))}
              <label className={`cart-choice ${cartId === "new" ? "active" : ""}`}>
                <input
                  type="radio"
                  name="cart"
                  value="new"
                  checked={cartId === "new"}
                  onChange={(e) => setCartId(e.target.value)}
                />
                <span className="cart-choice-name">+ New cart</span>
              </label>
              {cartId === "new" && (
                <input
                  className="dialog-input"
                  placeholder="Name the new cart, e.g. Weekend Trip"
                  value={newCartName}
                  maxLength={255}
                  autoFocus
                  onChange={(e) => setNewCartName(e.target.value)}
                />
              )}
            </div>
          )}
        </div>

        <div className="dialog-footer">
          <span className="dialog-total">
            Total <strong>{money(lineTotal)}</strong>
          </span>
          <div className="dialog-actions">
            <button type="button" className="ui-btn-secondary" onClick={onClose}>
              Cancel
            </button>
            <button type="submit" className="ui-btn-primary" disabled={!canSubmit}>
              {isSaving ? "Adding…" : "Add to cart"}
            </button>
          </div>
        </div>
      </form>
    </div>
  );
}
