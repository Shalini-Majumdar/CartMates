import * as React from "react";
import {
  createBrowserRouter,
  Navigate,
  Outlet,
  RouterProvider,
} from "react-router-dom";
import Login from "./Login";
import HomePage from "./HomePage";
import SelectedCart from "./SelectedCart";
import ShopPage from "./ShopPage";
import CheckoutPage from "./CheckoutPage";
import NavBar from "./NavBar";
import RequireAuth from "./RequireAuth";

// Every signed-in page shares the top bar.
function SignedInLayout() {
  return (
    <RequireAuth>
      <NavBar />
      <Outlet />
    </RequireAuth>
  );
}

const router = createBrowserRouter([
  {
    path: "/",
    element: <Login />,
  },
  {
    element: <SignedInLayout />,
    children: [
      { path: "/home", element: <ShopPage /> },
      { path: "/carts", element: <HomePage /> },
      { path: "/cart/:cartId", element: <SelectedCart /> },
      { path: "/checkout", element: <CheckoutPage /> },
      // Old address of the cart list, kept so bookmarks still work.
      { path: "/homepage", element: <Navigate to="/carts" replace /> },
    ],
  },
]);

export default function App() {
  return (
    <React.StrictMode>
      <RouterProvider router={router} />
    </React.StrictMode>
  );
}
