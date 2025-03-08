# DecorStream: Elegant Living Rentals Powered by Blockchain Technology  

## Overview  
DecorStream is a blockchain-based furniture rental platform designed to ensure transparency, security, and efficiency. By leveraging smart contracts, it automates rental agreements, verifies listings, and facilitates secure payments. The platform eliminates intermediaries, reduces costs, and enhances trust between renters and owners.  

## Key Features  

### *User Features*:  
✅ **Full-featured Shopping Cart** – Easily add, remove, and manage rental items.  
✅ **Review and Rating System** – Users can rate and review rented items.  
✅ **Top Products Carousel** – Highlights trending or featured rental items.  
✅ **Product Pagination** – Efficient browsing through rental listings.  
✅ **Product Search** – Quick and easy product lookup.  
✅ **User Profile with Orders** – Track rental history and manage ongoing rentals.  
✅ **Checkout Process** – Seamless checkout with shipping and payment options.  
✅ **Razorpay Payment Integration** – Secure online payments via Razorpay.  
✅ **Category Filter** – Browse items by category for easier selection.  
✅ **Addition of Variable Products** – Rent different product variations (sizes, colors, etc.).  

### *Admin Features*:  
🔹 **Product Management** – Add, edit, and delete rental listings.  
🔹 **Order Management** – View, update, and track rental transactions.  
🔹 **Mark Orders as Delivered** – Update order status to keep track of completed rentals.  

### *Additional Features*:  
📢 **Blog Posting** – Share updates, promotions, and news.  
📩 **Contact Page** – Enable user communication and inquiries.  
🎨 **Modern UI/UX Design** – Elegant and professional interface.  
📂 **Unlimited Products, Categories & Pages** – Scalable and flexible platform.  
⚙️ **Easy Management** – Intuitive admin controls for seamless operation.  

## Technologies Used  

### *Blockchain & Smart Contracts:*   
- **Solidity** – Programming language for writing smart contracts.  
- **Truffle** – Framework for testing and deploying smart contracts.  
- **Ganache** – Local blockchain for testing transactions.  

### *Web Development:*  
- **Django** – Backend framework for handling user management and business logic.  
- **HTML, CSS, JavaScript** – Frontend development for UI/UX.  
- **Bootstrap** – Responsive and modern UI design.  

### *Database & Storage:*  
- **SQLite3** – Lightweight database for storing user, product, and order data.  

### *Payment Integration:*  
- **Razorpay API** – Secure online transactions via UPI, debit/credit cards, and net banking.  

## How to Run the Project  

### *Prerequisites:*  
Ensure you have the following installed:  
- **Node.js & npm** (for Truffle and Ganache)  
- **Python 3.x** (for Django backend)  
- **MetaMask Wallet** (for blockchain transactions)  
- **SQLite3** (for database management)  

### Installation Steps:  
1. **Clone the Repository:**  
   ```bash
   git clone https://github.com/yourusername/DecorStream.git
   cd DecorStream
   ```  
2. **Set up the Backend (Django):**  
   ```bash
   pip install -r requirements.txt  
   python manage.py migrate  
   python manage.py runserver  
   ```  
3. **Deploy Smart Contracts:**  
   ```bash
   truffle compile  
   truffle migrate --network development  
   ```  
4. **Run Ganache for Local Blockchain:**  
   ```bash
   ganache-cli  
   ```  
5. **Start the Frontend:**  
   ```bash
   npm install  
   npm start  
   ```  

## Contributing 
Feel free to fork this repository and submit a pull request. Contributions are always welcome!  


