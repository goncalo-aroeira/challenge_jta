# Source Code Organization

This directory contains the source code for the Recommendation System.

## Structure

- **`config/`**: Configuration files.
  - `database.py`: Centralized database connection logic.

- **`etl/`**: Extract, Transform, Load scripts.
  - `load_json.py`: Loads product data from JSON to staging tables.
  - `load_excel.py`: Loads co-occurrence data from Excel to staging tables.
  - `process_data.py`: Processes raw data into final tables with feature engineering.

- **`recsys/`**: Recommendation System logic.
  - `tools.py`: Functions/Tools available for the Agent to query the database.

- **`agent/`**: LLM Agent implementation.
  - `core.py`: Main agent logic orchestrating Parser, Planner, and LLM.
  - `parser.py`: Intent parsing module using OpenAI Structured Outputs (Pydantic).
  - `planner.py`: Planning module that maps intents to tool executions.
  - `prompts.py`: System prompts and templates.

- **`frontend/`**: User Interface.
  - `app.py`: Streamlit chat application.

- **`utils/`**: Utility scripts.
  - `inspect_db.py`: Helper to inspect database tables.
  - `test_connection.py`: Helper to test database connection.

## How to Run

Run scripts as modules from the `part2` directory:

```bash
# Test connection
python -m src.utils.test_connection

# Run ETL pipeline
python -m src.etl.load_json
python -m src.etl.load_excel
python -m src.etl.process_data

# Run Agent (CLI)
python run_agent.py

# Run Frontend (Streamlit)
streamlit run src/frontend/app.py
```
