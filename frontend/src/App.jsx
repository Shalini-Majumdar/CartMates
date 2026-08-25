import * as React from "react";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import Login from "./Login";
import Cart from "./Cart";
import HomePage from "./HomePage";
import Product from "./Product";
import SelectedCart from "./SelectedCart";

const router = createBrowserRouter([
  {
    path: "/",
    element: <Login />,
  },
  {
    path: "/cart",
    element: <Cart />,
  },
  {
    path: "/homepage",
    element: <HomePage />,
  },
  {
    path: "/product",
    element: <Product />,
  },
  // {
  //   path: "/selectedcart",
  //   element: <SelectedCart />,
  // },
  {
    path: "/cart/:cartId",
    element: <SelectedCart />,
  },
]);

export default function App() {
  return (
    <React.StrictMode>
      <RouterProvider router={router} />
    </React.StrictMode>
  );
}
