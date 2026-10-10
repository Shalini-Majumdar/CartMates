import "./CheckoutPage.css";
import { useCallback, useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import ErrorPopup from "./Error";
import { apiFetch } from "./api";
import { money } from "./format";

const PLACEHOLDER_IMG =
  "https://www.svgrepo.com/show/508699/landscape-placeholder.svg";

// Simulated delivery pricing for the demo checkout.
const FREE_DELIVERY_FROM = 25;
const DELIVERY_FEE = 2.99;

const PAYMENT_METHODS = [
  { value: "upi", label: "UPI", hint: "Pay with any UPI app" },
  { value: "card", label: "Credit / debit card", hint: "Visa, Mastercard, RuPay" },
  { value: "netbanking", label: "Net banking", hint: "All major banks" },
  { value: "cod", label: "Cash on delivery", hint: "Pay when it arrives" },
];

const EMPTY_ADDRESS = {
  fullName: "",
  phone: "",
  line1: "",
  city: "",
  postalCode: "",
};

const deliveryFor = (subtotal) =>
  subtotal === 0 || subtotal >= FREE_DELIVERY_FROM ? 0 : DELIVERY_FEE;

export default function CheckoutPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const cartParam = searchParams.get("cart");

  const [carts, setCarts] = useState(null);
  const [items, setItems] = useState(null);
  const [address, setAddress] = useState(() => ({
    ...EMPTY_ADDRESS,
    fullName: localStorage.getItem("userName") || "",
  }));
  const [payment, setPayment] = useState("upi");
  const [triedSubmit, setTriedSubmit] = useState(false);
  const [isPlacing, setIsPlacing] = useState(false);
  const [receipt, setReceipt] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");

  // Re-read the carts whenever the chosen cart changes (including the navbar's
  // plain /checkout link), so totals are fresh and an old receipt is cleared.
  useEffect(() => {
    setReceipt(null);
    setTriedSubmit(false);
    apiFetch("/carts")
      .then((data) => setCarts(Array.isArray(data) ? data : []))
      .catch((err) => {
        setErrorMessage(err.message || "Could not load your carts");
        setCarts([]);
      });
  }, [cartParam]);

  const cart = carts?.find((c) => String(c.cart_id) === cartParam) || null;

  const loadItems = useCallback(async (cartId) => {
    setItems(null);
    try {
      const data = await apiFetch(`/carts/${cartId}/items`);
      setItems(Array.isArray(data) ? data : []);
    } catch (err) {
      setErrorMessage(err.message || "Could not load the cart");
      setItems([]);
    }
  }, []);

  useEffect(() => {
    if (cart && !receipt) loadItems(cart.cart_id);
  }, [cart, receipt, loadItems]);

  const chooseCart = (cartId) => {
    setSearchParams(cartId ? { cart: String(cartId) } : {});
  };

  const approved = (items || []).filter((i) => i.approved);
  const pending = (items || []).filter((i) => !i.approved);
  const subtotal = approved.reduce(
    (sum, i) => sum + Number(i.product.price) * i.quantity,
    0
  );
  const delivery = deliveryFor(subtotal);

  const missing = Object.entries({
    fullName: address.fullName.trim(),
    phone: address.phone.trim(),
    line1: address.line1.trim(),
    city: address.city.trim(),
    postalCode: address.postalCode.trim(),
  })
    .filter(([, v]) => !v)
    .map(([k]) => k);

  const placeOrder = async (e) => {
    e.preventDefault();
    setTriedSubmit(true);
    if (missing.length || approved.length === 0 || isPlacing) return;

    setIsPlacing(true);
    try {
      const data = await apiFetch(`/carts/${cart.cart_id}/checkout`, {
        method: "POST",
      });
      const itemsTotal = Number(data.total);
      const fee = deliveryFor(itemsTotal);
      setReceipt({
        ...data,
        delivery: fee,
        grandTotal: itemsTotal + fee,
        address: { ...address },
        paymentLabel: PAYMENT_METHODS.find((m) => m.value === payment)?.label,
      });
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (err) {
      setErrorMessage(err.message || "Could not place the order");
    } finally {
      setIsPlacing(false);
    }
  };

  const field = (name, label, props = {}) => (
    <label className={`co-field ${props.wide ? "wide" : ""}`}>
      <span>{label}</span>
      <input
        value={address[name]}
        onChange={(e) => setAddress((a) => ({ ...a, [name]: e.target.value }))}
        aria-invalid={triedSubmit && missing.includes(name)}
        className={triedSubmit && missing.includes(name) ? "invalid" : ""}
        {...props.input}
      />
    </label>
  );

  let content;

  if (receipt) {
    content = (
      <section className="co-card co-confirmation">
        <div className="co-check" aria-hidden="true">
          ✓
        </div>
        <h1>Order placed!</h1>
        <p className="co-muted">
          Thanks, {receipt.address.fullName}. This was a demo checkout, so no
          payment was taken.
        </p>
        <div className="co-order-meta">
          <div>
            <span>Order number</span>
            <strong>{receipt.order_number}</strong>
          </div>
          <div>
            <span>From cart</span>
            <strong>{receipt.cart_name}</strong>
          </div>
          <div>
            <span>Payment</span>
            <strong>{receipt.paymentLabel}</strong>
          </div>
        </div>

        <div className="co-receipt">
          {receipt.items.map((line) => (
            <div className="co-receipt-row" key={line.product_id}>
              <span>
                {line.quantity} × {line.product_name}
              </span>
              <span>{money(line.line_total)}</span>
            </div>
          ))}
          <div className="co-receipt-row co-muted">
            <span>Delivery</span>
            <span>{receipt.delivery ? money(receipt.delivery) : "Free"}</span>
          </div>
          <div className="co-receipt-row co-receipt-total">
            <span>Total</span>
            <span>{money(receipt.grandTotal)}</span>
          </div>
        </div>

        <p className="co-muted">
          Delivering to {receipt.address.line1}, {receipt.address.city}{" "}
          {receipt.address.postalCode}.
          {receipt.items_left_pending > 0 &&
            ` ${receipt.items_left_pending} item(s) still awaiting approval were left in the cart.`}
        </p>

        <div className="co-actions">
          <Link to="/home" className="ui-btn-primary">
            Continue shopping
          </Link>
          <Link to="/carts" className="ui-btn-secondary">
            Back to my carts
          </Link>
        </div>
      </section>
    );
  } else if (carts === null) {
    content = <div className="co-loading">Loading your carts…</div>;
  } else if (!cart) {
    content = (
      <section>
        <h1 className="co-title">Choose a cart to check out</h1>
        <p className="co-muted co-subtitle">
          Only approved items are bought. Items still awaiting approval stay in
          the cart.
        </p>
        {carts.length === 0 ? (
          <div className="co-card co-empty">
            <p>You don't have any carts yet.</p>
            <Link to="/home" className="ui-btn-primary">
              Start shopping
            </Link>
          </div>
        ) : (
          <div className="co-cart-grid">
            {carts.map((c) => (
              <button
                type="button"
                key={c.cart_id}
                className="co-cart-option"
                onClick={() => chooseCart(c.cart_id)}
              >
                <div className="co-cart-option-top">
                  <span className="co-cart-option-name">{c.cart_name}</span>
                  {c.is_shared && <span className="ui-tag">Shared</span>}
                </div>
                {c.cart_description && (
                  <span className="co-cart-option-desc">{c.cart_description}</span>
                )}
                <div className="co-cart-option-bottom">
                  <span className="co-muted">Approved total</span>
                  <strong>{money(c.total)}</strong>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    );
  } else {
    content = (
      <form className="co-layout" onSubmit={placeOrder} noValidate>
        <div className="co-main">
          <div className="co-heading-row">
            <h1 className="co-title">Checkout: {cart.cart_name}</h1>
            <button type="button" className="ui-link" onClick={() => chooseCart(null)}>
              Change cart
            </button>
          </div>

          <section className="co-card">
            <h2>1. Items</h2>
            {items === null ? (
              <div className="co-muted">Loading items…</div>
            ) : approved.length === 0 ? (
              <div className="co-empty-inline">
                <p>There are no approved items in this cart yet.</p>
                <Link to={`/cart/${cart.cart_id}`} className="ui-btn-secondary ui-btn-small">
                  Open the cart to approve items
                </Link>
              </div>
            ) : (
              <ul className="co-items">
                {approved.map((i) => (
                  <li key={i.cart_item_id}>
                    <img
                      src={i.product.image_url || PLACEHOLDER_IMG}
                      alt=""
                      onError={(e) => {
                        e.currentTarget.onerror = null;
                        e.currentTarget.src = PLACEHOLDER_IMG;
                      }}
                    />
                    <div className="co-item-info">
                      <span className="co-item-name">{i.product.product_name}</span>
                      <span className="co-muted">
                        {i.quantity} × {money(i.product.price)}
                      </span>
                    </div>
                    <span className="co-item-total">
                      {money(Number(i.product.price) * i.quantity)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            {pending.length > 0 && (
              <div className="co-pending">
                <span className="ui-tag ui-tag-warning">Not included</span>
                <span>
                  {pending.length} item(s) awaiting approval:{" "}
                  {pending.map((i) => i.product.product_name).join(", ")}.{" "}
                  <Link to={`/cart/${cart.cart_id}`}>Review in cart</Link>
                </span>
              </div>
            )}
          </section>

          <section className="co-card">
            <h2>2. Delivery address</h2>
            <div className="co-form-grid">
              {field("fullName", "Full name", { input: { autoComplete: "name" } })}
              {field("phone", "Phone number", {
                input: { type: "tel", autoComplete: "tel", inputMode: "tel" },
              })}
              {field("line1", "Address (house no., street, area)", {
                wide: true,
                input: { autoComplete: "street-address" },
              })}
              {field("city", "City", { input: { autoComplete: "address-level2" } })}
              {field("postalCode", "PIN / postal code", {
                input: { autoComplete: "postal-code", inputMode: "numeric" },
              })}
            </div>
            {triedSubmit && missing.length > 0 && (
              <p className="co-error">Please fill in the highlighted fields.</p>
            )}
          </section>

          <section className="co-card">
            <h2>3. Payment method</h2>
            <div className="co-demo-banner">
              <strong>Demo checkout.</strong> No payment gateway is connected, so
              nothing will be charged and no payment details are asked for.
            </div>
            <div className="co-payment-options">
              {PAYMENT_METHODS.map((m) => (
                <label
                  key={m.value}
                  className={`cart-choice ${payment === m.value ? "active" : ""}`}
                >
                  <input
                    type="radio"
                    name="payment"
                    value={m.value}
                    checked={payment === m.value}
                    onChange={(e) => setPayment(e.target.value)}
                  />
                  <span className="cart-choice-name">
                    {m.label}
                    <span className="co-payment-hint">{m.hint}</span>
                  </span>
                </label>
              ))}
            </div>
          </section>
        </div>

        <aside className="co-summary co-card">
          <h2>Order summary</h2>
          <div className="co-summary-row">
            <span>
              Items ({approved.reduce((n, i) => n + i.quantity, 0)})
            </span>
            <span>{money(subtotal)}</span>
          </div>
          <div className="co-summary-row">
            <span>Delivery</span>
            <span>{delivery ? money(delivery) : "Free"}</span>
          </div>
          {subtotal > 0 && delivery > 0 && (
            <p className="co-hint">
              Add {money(FREE_DELIVERY_FROM - subtotal)} more for free delivery.
            </p>
          )}
          <div className="co-summary-row co-summary-total">
            <span>Total</span>
            <span>{money(subtotal + delivery)}</span>
          </div>
          <button
            type="submit"
            className="ui-btn-primary co-place"
            disabled={isPlacing || items === null || approved.length === 0}
          >
            {isPlacing ? "Placing order…" : "Place order"}
          </button>
          <p className="co-hint">
            Placing the order removes the bought items from “{cart.cart_name}”.
          </p>
        </aside>
      </form>
    );
  }

  return (
    <>
      <ErrorPopup message={errorMessage} onClose={() => setErrorMessage("")} />
      <div className="checkout-page">
        <div className="checkout-inner">{content}</div>
      </div>
    </>
  );
}
