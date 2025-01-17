# Comparative Analysis Polimeromics

**Comparative Analysis Polimeromics** is a project designed to analyze complex biological data using an interactive dashboard built with Dash and Python. This repository includes a comparative analysis of two main databases: **BIOGRID** and **RCSB PDB**, focusing on Homo sapiens.

## Objective
The main goal is to provide a visual and interactive tool to explore biological data, identify patterns, and facilitate decision-making in scientific and research contexts.

## Key Features
- **PostgreSQL Connection**: Data is loaded directly from a PostgreSQL database.
- **Interactive Visualizations**: Histograms, scatter plots, box plots, and more, generated with Plotly.
- **Detailed Exploration**: Tabs for general, comparative, and customized analysis.
- **Smooth Navigation**: Built with Dash and Bootstrap components for an optimized user experience.

## Project Structure
```
Comparative Analysis Polimeromics/
│
├── dashboard.py         # Main dashboard code
├── requirements.txt     # Required dependencies
├── Procfile             # Configuration for Railway
├── README.md            # Project documentation
└── assets/              # Static files, if applicable
```

## Prerequisites
- **Python 3.8 or higher**
- Dependencies listed in `requirements.txt`

## Installation and Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your_username/Comparative-Analysis-Polimeromics.git
cd Comparative-Analysis-Polimeromics
```

### 2. Install Dependencies
Use `pip` to install the required dependencies:
```bash
pip install -r requirements.txt
```

### 3. Configure the Database
- Ensure you have access to the PostgreSQL database used in this project.
- Set the `DATABASE_URL` environment variable with the database connection URL:
  ```bash
  export DATABASE_URL=postgresql://user:password@host:port/database_name
  ```

### 4. Run the Dashboard
Start the local server:
```bash
python dashboard.py
```
Access the dashboard at [http://127.0.0.1:8000](http://127.0.0.1:8000).

## Deployment on Railway
1. Create a new project in Railway and link this repository.
2. Set the `DATABASE_URL` environment variable with the PostgreSQL database URL.
3. Railway will automatically detect the `Procfile` and deploy the application.

## Dashboard Usage
The dashboard is divided into three main tabs:

1. **General Overview**
   - Visualization of interaction distribution in BIOGRID.
   - Temperature and pH relationship in RCSB PDB.

2. **Comparative Analysis**
   - Comparison of key metrics such as oligomeric state and Matthews coefficient.

3. **Detailed Exploration**
   - Dynamic column selection to visualize specific distributions in both datasets.

## Screenshots
*(Include relevant screenshots of the dashboard in action)*

## Contribution
Contributions are welcome! Please follow these steps:
1. Fork this repository.
2. Create a new branch for your changes: `git checkout -b feature/new-feature`.
3. Commit your changes: `git commit -m 'Add new feature'`.
4. Push your changes: `git push origin feature/new-feature`.
5. Open a Pull Request.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Contact
For questions, feedback or access to the PostgreSQL database used in this project, please contact:
- **Name**: [Kent Valera Chirinos]
- **Email**: valerakent@yahoo.com
- **GitHub**: [https://github.com/your_username](https://github.com/kentvalerach)

---
Thank you for using Comparative Analysis Polimeromics! 🚀

