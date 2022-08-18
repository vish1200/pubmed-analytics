import pandas as pd
import glob
import os


# Get scores for columns
def get_completion_percentage(df: pd.DataFrame, column: str) -> float:
    empty_rows = df.loc[pd.isna(df[column])]
    # empty_rows = df.loc[df[column] == '']
    return round(((len(df) - len(empty_rows)) / len(df)) * 100, 1)


if __name__ == "__main__":
    os.chdir("./excel_output")
    for file in glob.glob("*.xlsx"):
        master_df = pd.read_excel(file, sheet_name='sheet1')

        print(f'\n{"-" * 48}\n')
        print(f'Results for {file}')

        # Get unique rows
        unique_df = master_df.drop_duplicates()
        print(f'There were {len(master_df) - len(unique_df)} duplicate rows in output\n')

        columns = list(master_df.columns)
        for col in columns:
            print(f'{col}: {get_completion_percentage(unique_df, col)}% complete')