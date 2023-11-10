import streamlit as st
import pandas as pd
import fuzzywuzzy.process as fuzz
import sys
import re
import yaml
from pages import page2

def page_1():

    st.title("Automated and Manual Cleaning")

    if 'df' not in st.session_state:
        st.session_state.df = None
    if 'reference_columns' not in st.session_state:
        st.session_state.reference_columns = []
    if 'mapped_columns' not in st.session_state:
        st.session_state.mapped_columns = {}
    if 'process_change_columns' not in st.session_state:
        st.session_state.process_change_columns = False
    if 'change_columns_list' not in st.session_state:
        st.session_state.change_columns_list = []

    def match_columns(df, reference_columns):
        matched_columns = {}  # Initialize the matched_columns dictionary
        input_columns = df.columns.tolist()
        for column in input_columns:
            matches = fuzz.extractBests(column, reference_columns)
            if matches:
                matched_columns[column] = matches
        return matched_columns
    if st.session_state.df is not None:
        if not st.session_state.mapped_columns:
            # Perform initial automated mapping only once
            matched_columns = match_columns(st.session_state.df, st.session_state.reference_columns)
            st.session_state.mapped_columns = matched_columns
            unique_identifier = 1  # Initialize a unique identifier
            for column, mapping in matched_columns.items():
                new_column_name = mapping[0][0]
                # Check for duplicate column names and add a unique identifier
                while new_column_name in st.session_state.df.columns:
                    new_column_name = f"{mapping[0][0]}_{unique_identifier}"
                    unique_identifier += 1
                st.session_state.df.rename(columns={column: new_column_name}, inplace=True)
        # Display the mapped columns
        st.subheader('Mapped Columns:')
        mapped_columns_text = ""
        for column_index, (column, mapping) in enumerate(st.session_state.mapped_columns.items()):
            mapped_columns_text += f"{column_index}. '{column}' is initially mapped to '{mapping[0][0]}'\n"
        st.text(mapped_columns_text)
        # Use st.form for user input
        with st.form(key='user_input_form'):
            st.subheader('Column Modification')
            change_columns_input = st.text_input("Enter a list of columns to modify (e.g., '0, 5, 7') or 'none' to skip:", key="change_columns_input")
            submit_button = st.form_submit_button("Submit")
        # Process form submission
        if submit_button:
            if change_columns_input.lower() != 'none':
                change_columns_list = [int(col.strip()) for col in change_columns_input.split(',') if col.strip()]
                st.session_state.change_columns_list = change_columns_list
                st.session_state.process_change_columns = True
            else:
                st.session_state.process_change_columns = False
        # Process user input
        if st.session_state.process_change_columns:
            change_columns_list = st.session_state.change_columns_list
            matched_columns = st.session_state.mapped_columns
            for column_index in change_columns_list:
                if 0 <= column_index and column_index < len(matched_columns):
                    selected_column = list(matched_columns.keys())[column_index]
                    st.write(f"Mapping options for column {column_index}: '{selected_column}':")
                    for j, (match, score) in enumerate(matched_columns[selected_column]):
                        st.write(f"  {j}. Map to '{match}' (Score: {score})")
                    match_choice = st.text_input("Enter the number for the mapping, or 'skip' to keep as is:", key=f"match_choice_{column_index}")
                    if match_choice.lower() != 'skip' and match_choice.isdigit():
                        match_index = int(match_choice)
                        if 0 <= match_index < len(matched_columns[selected_column]):
                            chosen_mapping = matched_columns[selected_column][match_index][0]
                            st.session_state.df.rename(columns={selected_column: chosen_mapping}, inplace=True)
                            st.write(f"Column {column_index}: '{selected_column}' has been mapped to '{chosen_mapping}'.")
                        else:
                            st.write("No changes have been made to the columns.")
                    else:
                        st.write("Invalid input. Please enter a valid number or 'skip'.")
        # Remove columns that are not in reference_columns in the updated DataFrame
        columns_to_remove = [col for col in st.session_state.df.columns if col not in st.session_state.reference_columns]
        st.session_state.df.drop(columns=columns_to_remove, inplace=True)
        # Add the "Last Name" column if it doesn't exist
        if "Last Name" not in st.session_state.df.columns:
            st.session_state.df["Last Name"] = ""
        # Display the updated DataFrame
        st.subheader('Updated DataFrame:')
        st.write(st.session_state.df)
    st.subheader("Automatic validations")
    def job_title(df):
        try:
            #   df = pd.read_excel(revision_file)
            missing_job = df['Title'].isna().sum()
            count = df['Title'].count() + missing_job
            percentage = (missing_job/count)
            if percentage <= 0.25:
                df = df[df['Title'].notna()]
                st.write ('All the records with missing information were deleted. Job Title has their 75% with valid information.')
                # return df
            else:
                st.write('In this dataset, less than 75% does not have Job Title completed')
                # return df
            return df
        except OSError as e:
                print(f"Unable to open {df} because: {e}", file=sys.stderr)
                return
    if st.session_state.df is not None:
        # Perform initial automated mapping only once
        cleaned_title = job_title(st.session_state.df)
        st.session_state.df = cleaned_title
    def split_name(df):
        # if df['Last Name'].isnull().values.any() == True:
        df = df.replace('[-| .,\/_]+',' ', regex = True)
        new = df["First Name"].str.split(" ", n=1, expand = True)
        df["First Name"] = new[0]
        df["Last Name"] = new[1]
            # return df
        # else:
        #     print("This database already has both Name and Last Name in different columns.")
            # return df
        return df
    if st.session_state.df is not None:
        # Perform initial automated mapping only once
        splitted_name = split_name(st.session_state.df)
        st.session_state.df = splitted_name
    def validate_names(data):
        data_temp = data
        data = data[data['First Name'].notna()]
        lenght = data['First Name'].str.len()
        mask = lenght >= 2
        data = data[mask]
        name_nulls = data_temp['First Name'].isna().sum()
        count_total_temp = data_temp['First Name'].count() + name_nulls
        count_rows = data['First Name'].count()
        percentage = count_rows/count_total_temp
        if percentage <= 0.25:
            st.write('All the records with missing information were deleted. Name has their 75% with information.')
            # return data
        else:
            st.write('In this dataset, less than 75% does not have a valid Name')
            # return data_temp
        return data
    if st.session_state.df is not None:
        # Perform initial automated mapping only once
        name_validation = validate_names(st.session_state.df)
        st.session_state.df = name_validation
    def validate_emails(df):
        # Extracting the Email and Lead Gatherer Email columns
        email_columns = ['Email']
        # Initialize valid email pattern
        pattern = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,4}'
        # Iterate through the specified columns
        for column in email_columns:
            column_name = f'{column} Validation'
            df[column_name] = df[column].apply(lambda email: bool(re.match(pattern, email)))
            df[column_name] = df[column_name].apply(lambda is_valid: 'Valid' if is_valid else 'Invalid')
        # Display the modified DataFrame
        return df
    if st.session_state.df is not None:
        # Perform initial automated mapping only once
        email_validation = validate_emails(st.session_state.df)
        st.session_state.df = email_validation
    
    def map_work_columns(data):
        data.columns = data.columns.str.replace('Work ', '')
        return data
    if st.session_state.df is not None:
        # Perform initial automated mapping only once
        work = map_work_columns(st.session_state.df)
        st.session_state.df = work
    
    # Display the updated DataFrame
    st.subheader('Updated DataFrame:')
    st.write(st.session_state.df)
    return st.session_state.df

if st.button("Next page"):
    if st.session_state.df is not None:
        page2.page_2()

