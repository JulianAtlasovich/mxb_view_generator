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
    elif any(keyword in sql_type_lower for keyword in ['decimal', 'float', 'numeric','money']):        
        return possible_types.index("MONEY")
    elif 'timestamp' in sql_type_lower:
        return possible_types.index("DATE")
    elif 'varchar' in sql_type_lower:
        return possible_types.index("VARCHAR")
    else:
        # Default to 0 if no match is found
        return 0

def parse_view_definition(view_definition):
    data = json.loads(view_definition)
    columns = []  
    table_name = data.get("name")

    for component in data.get("components", []):
        # Process dimensions
        for dim in component.get("dimensions", []):
            columns.append({
                "column_name": dim.get("id"),
                "column_type": dim.get("type"),
                "display_name": dim.get("header_text"),
                "dim_or_met": "Dimension"
            })

        # Process metrics
        for metric in component.get("metrics", []):
            columns.append({
                "column_name": metric.get("id"),
                "column_type": metric.get("type"),
                "display_name": metric.get("header_text"),
                "dim_or_met": "Metric"
            })

    return columns,table_name,data

def assume_dimension_or_metric(column_name,column_type):
    metric_types = ['int', 'float', 'decimal', 'numeric', 'money']
    sql_type_lower = column_type.lower()

    if 'id' not in column_name.lower() and any(metric in sql_type_lower for metric in metric_types):
        return 'Metric'
    else:
        return 'Dimension'
    
def convert_name_to_display_name(column_name):
    display_name = column_name.replace('_', ' ')
    display_name = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', display_name)
    display_name = display_name.title()
    
    return display_name

def parse_table_definition_postgres(table_def):
    match = re.search(r'CREATE TABLE\s+(?:\S+\.)?(\w+)\s*\(', table_def, re.IGNORECASE)
    if match:
        table_name = match.group(1)  # The table name is captured here
    else:
        table_name = "unknown_table"  # Default or error handling

    pattern = re.compile(r'\b"?(\w+)"?\s+(\w+)\b[^,]*')
    # Find all matches starting from the first opening parenthesis to avoid matching the table name
    start_pos = table_def.find('(')
    if start_pos == -1:
        return []  # Return an empty list if no column definitions are found
    column_definitions = table_def[start_pos:]
    matches = pattern.findall(column_definitions)

    columns = []
    column_names=[]
    for match in matches:
        column_name, column_type = match
        if column_name.upper() in ['PRIMARY', 'FOREIGN', 'UNIQUE', 'CHECK', 'NOT', 'NULL','CONSTRAINT']:
            continue
        columns.append({"column_name": column_name, "column_type": column_type,"display_name":convert_name_to_display_name(column_name),"dim_or_met":assume_dimension_or_metric(column_name,column_type)})
        column_names.append(column_name)
    
    return columns,table_name

# Function for SQL Server
def parse_table_definition_sqlserver(query):
    #TODO
    return "",""

# Function for PostgreSQL
def create_config(columns,name):
    st.write("---")
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
        with col2:
            type_options = ["VARCHAR", "INT", "DATE", "MONEY"]
            col_type = st.selectbox("", type_options, key='sb'+str(index),index= map_sql_type_to_index(type_options,row['column_type']))
            df.at[index, 'column_type'] = col_type  # Update the DataFrame with the selected option
        with col3:
            display_name = st.text_input("", value=row['display_name'], key='ti'+str(index))
            df.at[index, 'display_name'] = display_name  # Update the display name
        with col4:
            dim_or_met = st.selectbox("", ["Dimension", "Metric", "Ignore Column"], key='dom'+str(index),index=(0 if row['dim_or_met'] == "Dimension" else 1))
            df.at[index, 'dim_or_met'] = dim_or_met

    st.write("---")
    return df.to_dict(orient="records"),view_name

def parse_table_definition():
    table_definition = st.text_area("Enter your table definition:", height=150)
    database_option = st.selectbox("Choose your database:", ("PostgreSQL",""))
    columns,table_name = None,None

    if table_definition:
        if database_option == "SQL Server":
            columns,table_name = parse_table_definition_sqlserver(table_definition)
        if database_option == "PostgreSQL":
            columns,table_name = parse_table_definition_postgres(table_definition)
    return columns,table_name

def create_json_result(columns,name,previous_view_definition):
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

    if previous_view_definition:
        previous_view_definition['components'][0]['metrics'] = metrics
        previous_view_definition['components'][0]['dimensions'] = dimensions
        json_object = previous_view_definition            
    else:
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
    return json_object

if __name__ == "__main__":
    st.title("MxB cloud view generator")
    input_option = st.selectbox("What do you want to do?", ("convert SQL definition into view","Edit MxB view"))
    if input_option=="convert SQL definition into view":
        columns,table_name = parse_table_definition()        
        if columns:
            updated_columns,view_name = create_config(columns,table_name)
            result = create_json_result(updated_columns,view_name,None)    
            st.write("**view definition**")
            st.write(result)
    elif input_option=="Edit MxB view":
        view_definition = st.text_area("Enter your view json definition:", height=150)
        if view_definition:
            columns,table_name,previous_view_definition = parse_view_definition(view_definition)
            updated_columns,view_name = create_config(columns,table_name)
            result = create_json_result(updated_columns,view_name,previous_view_definition)   
            st.write("**view definition**")
            st.write(result)
            
