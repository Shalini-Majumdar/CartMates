import { Navigate, useLocation } from "react-router-dom";
import { getToken } from "./api";

/**
 * Gate for routes that need a signed-in user.
 *
 * This is a convenience only — it stops the app rendering a page whose every
 * request would fail. The real check is server-side: every cart route resolves
 * the caller from their bearer token and verifies cart membership.
 */
export default function RequireAuth({ children }) {
  const location = useLocation();

  if (!getToken()) {
    return <Navigate to="/" replace state={{ from: location.pathname }} />;
  }

  return children;
}
