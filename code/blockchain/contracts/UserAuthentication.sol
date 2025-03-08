// SPDX-License-Identifier: MIT
pragma solidity  >= 0.5.16 <= 0.5.16;

contract UserAuthentication {
    struct User {
        bool isRegistered;
        string email;
    }

    mapping(address => User) public users;
    mapping(string => address) private emailToAddress;  // Email to address mapping

    event UserRegistered(address indexed userAddress, string email);

    function register(
        string memory _email,
        string memory _firstName,
        string memory _lastName,
        string memory _phoneNumber,
        string memory _password
    ) public {
        require(!users[msg.sender].isRegistered, "User already registered");
        require(emailToAddress[_email] == address(0), "Email already in use"); // Prevent duplicate emails

        users[msg.sender] = User(true, _email);
        emailToAddress[_email] = msg.sender; // Store email → address mapping

        emit UserRegistered(msg.sender, _email);
    }

    function isUserRegistered(string memory _email) public view returns (bool) {
        return emailToAddress[_email] != address(0); // Returns true if email is mapped
    }

    function getAddressByEmail(string memory _email) public view returns (address) {
        require(emailToAddress[_email] != address(0), "Email not registered");
        return emailToAddress[_email];
    }
}