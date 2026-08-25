import "./CartPopup.css";
import { useState, useEffect } from "react";

export default function CartPopup({ onClose, onSubmit }) {
  const userId = localStorage.getItem("userId");
  const [cartTitle, setCartTitle] = useState("");
  const [cartDescription, setCartDescription] = useState("");
  const [allUsers, setAllUsers] = useState([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [selectedFriends, setSelectedFriends] = useState([]);
  const [isShared, setIsShared] = useState(false);

  // Fetch all users on mount
  //   useEffect(() => {
  //     const fetchUsers = async () => {
  //       try {
  //         const res = await fetch("http://localhost:5000/api/get_users");
  //         const data = await res.json(); // Expected: [{ user_id, user_name }]
  //         setAllUsers(data);
  //         setFilteredUsers(data);
  //       } catch (error) {
  //         console.error("Error fetching users:", error);
  //         setAllUsers([]);
  //       }
  //     };

  //     fetchUsers();
  //   }, []);

  useEffect(() => {
    // Dummy users
    const dummyUsers = [
      { user_id: 1, user_name: "Shaunak" },
      { user_id: 2, user_name: "Riya" },
      { user_id: 3, user_name: "Aryan" },
      { user_id: 4, user_name: "Tanvi" },
      { user_id: 5, user_name: "Aman" },
      { user_id: 6, user_name: "Sanya" },
    ];

    setAllUsers(dummyUsers);
    setFilteredUsers(dummyUsers);
  }, []);

  // Handle search input change
  useEffect(() => {
    const results = allUsers.filter((user) =>
      user.user_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
    setFilteredUsers(results);
  }, [searchTerm, allUsers]);

  const toggleFriend = (friend) => {
    if (selectedFriends.find((f) => f.user_id === friend.user_id)) {
      setSelectedFriends((prev) =>
        prev.filter((f) => f.user_id !== friend.user_id)
      );
    } else {
      setSelectedFriends((prev) => [...prev, friend]);
    }
  };

  const handleSubmit = () => {
    const cartPayload = {
      cart_name: cartTitle,
      cart_description: cartDescription,
      shared_with: isShared ? selectedFriends.map((f) => f.user_id) : [],
      is_shared: isShared ? 1 : 0,
      // user_id: userId,
    };
    onSubmit(cartPayload);
    onClose();
  };

  return (
    <div className="popup-overlay">
      <div className="popup">
        <div className="popup-header">
          <h2>Configure Cart</h2>
          <button className="close-btn" onClick={onClose}>
            &times;
          </button>
        </div>

        <div className="popup-content">
          <div className="form-group">
            <label htmlFor="cartTitle">Cart Title</label>
            <input
              type="text"
              id="cartTitle"
              className="form-control"
              placeholder="Enter cart title..."
              value={cartTitle}
              onChange={(e) => setCartTitle(e.target.value)}
            />
          </div>

          <div className="form-group">
            <label htmlFor="cartDescription">Cart Description</label>
            <textarea
              id="cartDescription"
              className="form-control"
              placeholder="Enter cart description..."
              value={cartDescription}
              onChange={(e) => setCartDescription(e.target.value)}
            ></textarea>
          </div>

          <div className="form-group">
            <label>
              <input
                type="checkbox"
                checked={isShared}
                onChange={(e) => setIsShared(e.target.checked)}
              />
              &nbsp;Share this cart with friends
            </label>
          </div>

          {isShared && (
            <div className="search-section">
              <label htmlFor="friendSearch">Add Friends</label>
              <div className="search-container">
                <span className="search-icon">🔍</span>
                <input
                  type="text"
                  id="friendSearch"
                  className="search-input"
                  placeholder="Search friends..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                />
                <div
                  className={`search-results ${
                    searchTerm.trim() !== "" && filteredUsers.length > 0
                      ? "show"
                      : ""
                  }`}
                >
                  {filteredUsers.map((user) => (
                    <div
                      key={user.user_id}
                      className={`search-item ${
                        selectedFriends.some((f) => f.user_id === user.user_id)
                          ? "selected"
                          : ""
                      }`}
                      onClick={() => toggleFriend(user)}
                    >
                      {user.user_name}
                    </div>
                  ))}
                  {filteredUsers.length === 0 && (
                    <div className="no-results">No users found</div>
                  )}
                </div>
              </div>

              <div className="selected-friends">
                {selectedFriends.map((friend) => (
                  <span key={friend.user_id} className="friend-pill">
                    {friend.user_name}
                    <button onClick={() => toggleFriend(friend)}>×</button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="popup-footer">
          <button className="btn btn-secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="btn btn-secondary" onClick={handleSubmit}>
            Add New Cart
          </button>
        </div>
      </div>
    </div>
  );
}
