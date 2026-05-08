# Schedulo - Automated Timetable Generation System

Schedulo is a web-based comprehensive timetable generation system. It automates the scheduling of lectures and practical labs for educational institutions, considering complex constraints such as faculty workload, lab availability, and class structures.

## 🚀 Features

- **Automated Timetable Generation**: Automatically creates conflict-free schedules for practicals and lectures using specialized constraint-solving algorithms.
- **Role-Based Access Control**: Different views and capabilities for Administrators and standard Faculty users. Secure JWT-based authentication.
- **Resource Management**: 
  - Manage faculty profiles, workloads, and constraints.
  - Manage laboratory availability, capacities, and types.
  - Define class structures, subjects, and schedules.
- **Interactive Dashboards**: Clear, dynamic visual representation of timetables for classes, individual faculties, and labs.
- **Constraint Handling**: Add custom constraints (e.g., faculty unavailability on specific days, preferred lab timings) dynamically.
- **Secure Data Storage**: Stores all institutional data persistently using MongoDB.

---

## 🛠️ Technology Stack

**Frontend:**
- [React](https://reactjs.org/) with [Vite](https://vitejs.dev/)
- [Tailwind CSS](https://tailwindcss.com/) for styling
- [React Router](https://reactrouter.com/) for navigation
- [Lucide React](https://lucide.dev/) for iconography
- [Axios](https://axios-http.com/) for API communication

**Backend:**
- [Python](https://www.python.org/) / [Flask](https://flask.palletsprojects.com/)
- [MongoDB](https://www.mongodb.com/) (using PyMongo)
- [PyJWT](https://pyjwt.readthedocs.io/) for secure token-based authentication
- [Flask-CORS](https://flask-cors.readthedocs.io/)

---

## 📂 Project Structure

```
TimeTable/
├── Backend/                 # Python/Flask Backend API
│   ├── modules/             # Core business logic (auth, handlers, generators)
│   ├── scripts/             # Utility and seed scripts
│   ├── app.py               # Main Flask application entry point
│   ├── config.py            # App configurations & DB setup
│   ├── requirements.txt     # Python dependencies
│   └── .env                 # Backend environment variables
│
├── Frontend/                # React/Vite Frontend Application
│   ├── src/                 # React source code (components, services, contexts)
│   ├── public/              # Static assets
│   ├── package.json         # Node.js dependencies and scripts
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── vite.config.ts       # Vite bundler configuration
│   └── .env                 # Frontend environment variables
│
└── README.md                # Project documentation
```

---

## ⚙️ Setup and Installation

### Prerequisites
- [Node.js](https://nodejs.org/) (v16+)
- [Python](https://www.python.org/) (v3.9+)
- [MongoDB](https://www.mongodb.com/) (Local or Atlas)

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd Backend
   ```
2. (Optional but recommended) Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create a `.env` file in the `Backend` folder and define your environment variables:
   ```env
   MONGO_URI=mongodb://localhost:27017/schedulo
   SECRET_KEY=your_super_secret_jwt_key
   ```
5. Run the Flask server:
   ```bash
   python app.py
   ```
   *The backend will typically run on `http://127.0.0.1:5000`.*

### 2. Frontend Setup

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd Frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Create a `.env` file in the `Frontend` folder (if applicable) for your backend API base URL:
   ```env
   VITE_API_URL=http://127.0.0.1:5000/api
   ```
4. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will typically run on `http://localhost:5173`.*

---

## 🔄 Workflow & Usage

To successfully generate and view timetables using the Schedulo system, administrators should follow these steps in order:

### 1. Data Initialization
*   **Manage Faculty:** Add all faculty members who will be taking classes.
*   **Manage Labs:** Add all computer labs, physical labs, and workshops, defining their capacity and specific constraints.
*   **Define Class Structure:** Setup departments, years, semesters, and division/batch configurations.
*   **Assign Subjects:** Define theory and practical subjects for each class structure.

### 2. Workload & Constraints Allocation
*   **Assign Workload:** Map faculty members to specific subjects (theory and practicals) along with the associated classes.
*   **Set Constraints:** (Optional) Add constraints regarding faculty availability, day-offs, or fixed lecture timings.

### 3. Timetable Generation
*   **Generate Practical Timetable:** The system first allocates practical batches to appropriate labs, avoiding clashes.
*   **Generate Lecture Timetable:** The system then schedules theory lectures in available free slots.

### 4. Review & Export
*   **Dashboard Views:** View the generated timetables via the Class, Faculty, or Lab Timetable dashboards.
*   **Conflict Resolution:** If any clashes are highlighted, manually adjust constraints or workloads and regenerate.

---

## 🤝 Contributing

When contributing to this project, please follow these guidelines:
1. Ensure the backend logic strictly follows the modular structure in `Backend/modules/`.
2. Add new React components in `Frontend/src/components/` and define any new API calls in a dedicated service file under `Frontend/src/services/`.
3. Test timetable generation functions thoroughly as they consist of complex constraint validations.

## 📝 License

This project is developed for educational and academic scheduling purposes.
