import streamlit as st
import json
import re
import pandas as pd

def map_sql_type_to_index(possible_types, sql_type):
    # Normalize the sql_type to lowercase for case-insensitive comparison
    sql_type_lower = sql_type.lower()
    
    # Check for each condition and return the appropriate index
    if 'int' in sql_type_lower:
        return possible_types.index("INT")
    elif any(keyword in sql_type_lower for keyword in ['decimal', 'float', 'numeric']):        
        return possible_types.index("MONEY")
    elif 'timestamp' in sql_type_lower:
        return possible_types.index("DATE")
    elif 'varchar' in sql_type_lower:
        return possible_types.index("VARCHAR")
    else:
        # Default to 0 if no match is found
        return 0


def parse_table_definition_postgres(table_def):
    #match table name
    match = re.search(r'CREATE TABLE\s+(?:\S+\.)?(\w+)\s*\(', table_def, re.IGNORECASE)
    if match:
        table_name = match.group(1)  # The table name is captured here
    else:
        table_name = "unknown_table"  # Default or error handling
    
    # Extract column definitions after the "CREATE TABLE" statement, ignoring constraints and modifiers
    pattern = re.compile(r'\b"?(\w+)"?\s+(\w+)\b[^,]*')
    
    # Find all matches starting from the first opening parenthesis to avoid matching the table name
    start_pos = table_def.find('(')
    if start_pos == -1:
        return []  # Return an empty list if no column definitions are found

    # Extract the substring that likely contains the column definitions
    column_definitions = table_def[start_pos:]
    
    matches = pattern.findall(column_definitions)

    # Construct a list of dictionaries for each column, excluding entries that are clearly not column definitions
    columns = []
    column_names=[]
    for match in matches:
        column_name, column_type = match
        # Exclude common SQL keywords that might still be captured despite the regex refinement
        if column_name.upper() in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'NOT', 'NULL','CONSTRAINT']:
            continue
        columns.append({"column_name": column_name, "column_type": column_type,"display_name":column_name,"dim_or_met":"Dimension"})
        column_names.append(column_name)
    
    #tg = st.checkbox('show extracted columns and types')
    #if tg:
        #st.write(columns)
    #os.write(1,columns)
    return columns,table_name

# Function for SQL Server
def parse_table_definition_sqlserver(query):
    #TODO
    return "",""

# Function for PostgreSQL
def create_config(columns,name):
    st.markdown("**Configuration**")
    view_name = st.text_input("View Name:", name)

    df = pd.DataFrame(columns)
    col1_title, col2_title, col3_title, col4_title = st.columns(4)
    with col1_title:
        st.markdown("**Column Name**")
    with col2_title:
        st.markdown("**Column Type**")
    with col3_title:
        st.markdown("**Display Name**")
    with col4_title:
        st.markdown("**Dimension / Metric**")

    for index, row in df.iterrows():
        col1, col2, col3, col4 = st.columns(4)    
        with col1:
            display_name = st.text_input("", value=row['column_name'], key='cn'+str(index), disabled=True)
            #st.text(row['column_name'])
        with col2:
            type_options = ["VARCHAR", "INT", "DATE", "MONEY"]
            col_type = st.selectbox("", type_options, key='sb'+str(index),index= map_sql_type_to_index(type_options,row['column_type']))
            df.at[index, 'column_type'] = col_type  # Update the DataFrame with the selected option
        with col3:
            display_name = st.text_input("", value=row['display_name'], key='ti'+str(index))
            df.at[index, 'display_name'] = display_name  # Update the display name
        with col4:
            dim_or_met = st.selectbox("", ["Dimension", "Metric", "Ignore Column"], key='dom'+str(index))
            df.at[index, 'dim_or_met'] = dim_or_met

    st.write("---")
    # Button to save the configuration
    #if st.button("Save Configuration"):
        # Convert DataFrame to JSON to save the configuration
    return df.to_dict(orient="records"),view_name
    #create_json_result(updated_columns,name)    

def create_json_result(columns,name):
    dimensions = []
    metrics = []
    for column in columns:
        if column["dim_or_met"] == "Dimension":
            dimension = {
                "id": column["column_name"],
                "type": column["column_type"],
                "index": 0,
                "width": "120",
                "format": "",
                "prefix": "",
                "visible": True,
                "field_id": column["column_name"],
                "data_align": "center",
                "filter_text": "",
                "header_text": column["display_name"],
                "column_align": "center",
                "default_filter": ""
            }
            dimensions.append(dimension)
        if column["dim_or_met"] == "Metric":
            metric = {
                "id": column["column_name"],
                "type": column["column_type"],
                "index": 0,
                "width": "120",
                "format": "",
                "prefix": "",
                "visible": True,
                "function":"sum",
                "totalize":True,
                "field_id": column["column_name"],
                "data_align": "center",
                "filter_text": "",
                "header_text": column["display_name"],
                "column_align": "center",
                "default_filter": ""
            }
            metrics.append(metric)


    json_object = {
        "name": name,
        "filters": [],
        "components": [
            {
                "name": name + "_grid",
                "type": "grid",
                "orders": [],
                "filters": [],
                "metrics": metrics,
                "hasnotes": False,
                "drilldown": "",
                "dimensions": dimensions,
                "data_source": name,
                "description": "",
                "drillthrough": "",
                "has_checkbox": False
            }
        ],
        "drilldowns": [],
        "description": "",
        "display_props": {
            "tab": "analysis",
            "name": name,
            "order": 99,
            "show_on_dashboard": True
        },
        "drillthroughs": []
    }

    #json_output = json.dumps(json_object, indent=4)

    return json_object

# Streamlit UI
st.title("MxB cloud view generator")
table_definition = st.text_area("Enter your table definition:", height=150)
database_option = st.selectbox("Choose your database:", ("PostgreSQL",""))
st.write('---')

if table_definition:
    if database_option == "SQL Server":
        columns,table_name = parse_table_definition_sqlserver(table_definition)
    if database_option == "PostgreSQL":
        columns,table_name = parse_table_definition_postgres(table_definition)
    
    updated_columns,view_name = create_config(columns,table_name)
    
    result = create_json_result(updated_columns,view_name)

    st.text_area("Json view def:", value=json.dumps(result, indent=4), height=250, key="result")
