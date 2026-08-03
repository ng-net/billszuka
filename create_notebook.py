import json
import pandas as pd

def generate_sample_analytics_notebook():
    notebook_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    "# BILLSzuka Data Analytics & Gemini Exploration Notebook\n",
                    "This notebook provides quick Python analytics, DuckDB aggregation, and visualization for CSV data ingested in the BILLSzuka workspace."
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "metadata": {},
                "outputs": [],
                "source": [
                    "import pandas as pd\n",
                    "import duckdb\n",
                    "\n",
                    "# Load active dataset\n",
                    "df = pd.read_csv('data/sales_data.csv')\n",
                    "print(f'Successfully loaded dataset with {len(df)} rows.')\n",
                    "df.head()"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# Execute DuckDB Aggregations\n",
                    "con = duckdb.connect()\n",
                    "con.register('sales', df)\n",
                    "summary = con.execute('''\n",
                    "    SELECT Region, Category, COUNT(*) as Count, SUM(Amount_USD) as Total_Revenue\n",
                    "    FROM sales\n",
                    "    GROUP BY Region, Category\n",
                    "    ORDER BY Total_Revenue DESC\n",
                    "''').df()\n",
                    "summary"
                ]
            }
        ],
        "metadata": {
            "language_info": {
                "name": "python"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    with open("analytics_exploration.ipynb", "w") as f:
        json.dump(notebook_content, f, indent=2)

if __name__ == "__main__":
    generate_sample_analytics_notebook()
