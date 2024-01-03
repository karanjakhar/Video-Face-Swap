import React from "react";

const Footer = () => {
  const footerStyle = {
    color: "white",
    backgroundColor: "#000",
    padding: "10px 20px",
    textAlign: "center",
  };

  return (
    <footer style={footerStyle}>
      <p>
        &copy; {new Date().getFullYear()} Video Face Swap. All rights reserved.
      </p>
    </footer>
  );
};

export default Footer;
