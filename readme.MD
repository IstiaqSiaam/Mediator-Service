# Mediator Service
  - This service is responsible for handling the communication between the client and the Cottage Booking System.

# API Endpoints
  - /get_rdg (Post Request) - This endpoint is used to get the RDG graph from the Cottage Booking System.
  - /book_cottage (Post Request) - This endpoint is used to book cottages. 

# Prerequisites
  - Python 3.10+
  - Flask

# Installation
### Steps

1. Clone the repository
  ```
2. Create a virtual environment ad activate it
  ```bash
  python3.10 -m venv venv   
  source venv/bin/activate  # On Windows, use: venv\Scripts\activate
 ```
 3. Install the dependencies
 ```bash
 pip install -r requirements.txt
 ```
 4. Run the application
 ```bash
 python mediator_service.py
 ```
 ```bash
 python fake_remote_service.py
 ```

 5. Open your browser and go to http://localhost:5000/ for the mediator and put http://localhost:5002/CottageBookingService in the remote URL
 
