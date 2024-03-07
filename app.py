import streamlit as st
import json
import re


def parse_table_definition_postgres(table_def):
    # Extract column definitions after the "CREATE TABLE" statement, ignoring constraints and modifiers
    # We aim to capture the column name and the primary data type directly following it
    
    # Adjust regex to capture column names and primary data types while excluding constraints and modifiers
    pattern = re.compile(r'\b(\w+)\s+(\w+)(?:\([^)]+\))?')
    
    # Find all matches starting from the first opening parenthesis to avoid matching the table name
    start_pos = table_def.find('(')
    if start_pos == -1:
        return []  # Return an empty list if no column definitions are found

    # Extract the substring that likely contains the column definitions
    column_definitions = table_def[start_pos:]
    
    matches = pattern.findall(column_definitions)

    # Construct a list of dictionaries for each column, excluding entries that are clearly not column definitions
    columns = []
    for match in matches:
        column_name, column_type = match
        # Exclude common SQL keywords that might still be captured despite the regex refinement
        if column_name.upper() in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'NOT', 'NULL']:
            continue
        columns.append({"column_name": column_name, "column_type": column_type})

    return columns


# Example usage
table_definition = """
CREATE TABLE example_table (
    id INTEGER PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    age INTEGER NOT NULL,
    email TEXT UNIQUE
);
"""

parsed_columns = parse_table_definition_postgres(table_definition)
st.write(parsed_columns)

# Function for SQL Server
def query_sql_server(query):
    # Your logic here. This is just a placeholder return statement.
    return {"source": "SQL Server", "query": query}

# Function for PostgreSQL
def query_postgresql(query):
    # Your logic here. This is just a placeholder return statement.
    return {"source": "PostgreSQL", "query": query}

# Streamlit UI
st.title("MxB cloud view generator")

# Text input box for the query
user_query = st.text_area("Enter your table definition:", height=150)

# Dropdown for database selection
database_option = st.selectbox("Choose your database:", ("SQL Server", "PostgreSQL"))

# Button to perform the action
if st.button("Create"):
    # Call the respective function based on the dropdown selection
    if database_option == "SQL Server":
        result = query_sql_server(user_query)
    else:
        result = query_postgresql(user_query)
    
    # Display the result in a text area for easy copy-pasting
    st.text_area("Formatted Query:", value=json.dumps(result, indent=4), height=250, key="result")
