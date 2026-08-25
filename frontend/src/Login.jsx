import "./Login.css";
import { motion } from "framer-motion";
import { Link, useNavigate } from "react-router-dom";
import { useState } from "react";
import GridMotion from "./GridMotion";

export default function Login(props) {
  const [isSignup, setIsSignup] = useState(true);
  const [email, setEmail] = useState("");
  const [user_name, setUsername] = useState(""); // for signup
  const [passwd, setPassword] = useState("");
  const [confirm_passwd, setConfirmPassword] = useState(""); // for signup
  const [errorMessage, setErrorMessage] = useState("");
  const navigate = useNavigate();

  const items = [
    "Item 1",
    "https://plus.unsplash.com/premium_photo-1681760550122-772c6b3a5680?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8YmVkJTIwcGlsbG93fGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1523381294911-8d3cead13475?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8OHx8dCUyMHNoaXJ0fGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1599623560574-39d485900c95?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8dG95c3xlbnwwfHwwfHx8MA%3D%3D",
    "https://images.unsplash.com/photo-1583947215259-38e31be8751f?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8Y2xlYW5pbmclMjBwcm9kdWN0fGVufDB8fDB8fHww",
    "Item 6",
    "Item 7",
    "Item 8",
    "https://plus.unsplash.com/premium_photo-1683120793196-0797cec08a7d?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MXx8YmF0dGVyeXxlbnwwfHwwfHx8MA%3D%3D",
    "https://images.unsplash.com/photo-1517336714731-489689fd1ca8?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8bWFjYm9va3xlbnwwfHwwfHx8MA%3D%3D",
    "https://9to5mac.com/wp-content/uploads/sites/6/2024/09/AirPods-hearing-aid-feature-is-going-to-challenge-social-norms.jpg?quality=82&strip=all&w=1600",
    "https://images.unsplash.com/photo-1606144042614-b2417e99c4e3?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8cGxheXN0YXRpb258ZW58MHx8MHx8fDA%3D",
    "https://images.unsplash.com/photo-1688384452579-a90e7a7f1aff?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTl8fGJlZCUyMHNoZWV0fGVufDB8fDB8fHww",
    "Item 14",
    "Item 15",
    "https://images.unsplash.com/photo-1650094980789-b0121916e666?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8N3x8d2FsbCUyMGNsb2NrfGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1628329567705-f8f7150c3cff?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8Ymx1ZXRvb3RoJTIwaGVhZHBob25lc3xlbnwwfHwwfHx8MA%3D%3D",
    "https://images.unsplash.com/photo-1603791239531-1dda55e194a6?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTJ8fGFwcGxlJTIwaXBob25lfGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1731132198530-e4b2dc51d511?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8N3x8c2hvZXMlMjBuaWtlfGVufDB8fDB8fHww",
    "https://images.unsplash.com/photo-1513506003901-1e6a229e2d15?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8bGFtcHxlbnwwfHwwfHx8MA%3D%3D",
    "Item 21",
    "Item 22",
    "Item 23",
    "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8NHx8Ym9va3N8ZW58MHx8MHx8fDA%3D",
    "https://images.unsplash.com/photo-1615873968403-89e068629265?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8MTJ8fGhvbWUlMjBkZWNvcnxlbnwwfHwwfHx8MA%3D%3D",
    "https://images.unsplash.com/photo-1621797064712-2ed3a36fc009?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8bWFrZSUyMHVwJTIwcHJvZHVjdHN8ZW58MHx8MHx8fDA%3D",
    "https://images.unsplash.com/photo-1568871391149-449702439177?fm=jpg&q=60&w=3000&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxzZWFyY2h8Mnx8c3RhdGlvbmFyeXxlbnwwfHwwfHx8MA%3D%3D",

    // Add more items as needed
  ];

  const handleLogin = async () => {
    if (!email || !passwd) {
      setErrorMessage("Please enter email and password.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, passwd }),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("userId", data.user_id);
        localStorage.setItem("userName", data.user_name);
        navigate("/homepage", { state: { userId: data.user_id } });
      } else {
        const err = await res.json();
        setErrorMessage(err.message || "Login failed");
      }
    } catch (error) {
      setErrorMessage("Something went wrong. Try again.");
    }
  };

  const handleSignup = async () => {
    if (!email || !passwd || !user_name || !confirm_passwd) {
      setErrorMessage("All fields are required.");
      return;
    }

    if (passwd !== confirm_passwd) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    try {
      const res = await fetch("http://localhost:8000/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, user_name, passwd, confirm_passwd }),
      });

      const data = await res.json();

      if (res.ok) {
        localStorage.setItem("userId", data.user_id);
        localStorage.setItem("userName", data.user_name);
        navigate("/homepage", { state: { userId: data.user_id } });
      } else {
        const err = await res.json();
        setErrorMessage(err.message || "Signup failed");
      }
    } catch (error) {
      setErrorMessage("Something went wrong. Try again.");
    }
  };

  return (
    <>
      <div className="default-login login-body">
        <div className="default-login login-left">
          <GridMotion items={items} />
        </div>
        <div className="default-login login-right">
          <motion.div
            className="default-login login-main"
            initial={{ y: -300, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 1.3, ease: "easeOut" }}
          >
            <div className="default-login login-title">
              {!isSignup ? "Create Account" : "Welcome Back"}
            </div>
            <div
              className={
                isSignup
                  ? "default-login login-user-div hidden"
                  : "default-login login-user-div"
              }
            >
              <input
                type="text"
                className="default-login login signup"
                placeholder="Username"
                value={user_name}
                onChange={(e) => setUsername(e.target.value)}
              ></input>
            </div>
            <div className="default-login login-user-div">
              <input
                type="text"
                className="default-login login"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              ></input>
            </div>
            <div className="default-login login-user-div">
              <input
                type="password"
                className="default-login login"
                placeholder="Password"
                value={passwd}
                onChange={(e) => setPassword(e.target.value)}
              ></input>
            </div>
            <div
              className={
                isSignup
                  ? "default-login login-password-div hidden"
                  : "default-login login-password-div"
              }
            >
              <input
                type="password"
                className="default-login login signup"
                placeholder="Confirm Password"
                value={confirm_passwd}
                onChange={(e) => setConfirmPassword(e.target.value)}
              ></input>
            </div>

            {errorMessage && (
              <div className="default-login login-error">{errorMessage}</div>
            )}

            <div className="default-login login-button-div">
              {/* <Link to="/homepage" className="default-login login-button"> */}
              <button
                className="default-login login-button"
                type="submit"
                onClick={!isSignup ? handleSignup : handleLogin}
              >
                {!isSignup ? "Sign Up" : "Log In"}
              </button>
              {/* </Link> */}
            </div>
            {isSignup ? (
              <div className="default-login login-footer">
                Don't have an account? &nbsp;
                <span
                  style={{ cursor: "pointer" }}
                  onClick={() => {
                    setErrorMessage("");
                    setIsSignup(!isSignup);
                  }}
                >
                  Sign Up!
                </span>
              </div>
            ) : (
              <span
                style={{ cursor: "pointer", color: "#3a7ff9" }}
                onClick={() => {
                  setErrorMessage("");
                  setIsSignup(!isSignup);
                }}
              >
                Back to Login
              </span>
            )}
          </motion.div>
        </div>
      </div>
    </>
  );
}
