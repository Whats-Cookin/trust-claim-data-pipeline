import pandas as pd

# Read the CSV file
df = pd.read_csv("../crowdsupply-demo5.csv")


# Function to clean and separate backers and their locations
def extract_backers_and_locations(backers_str):
    if pd.isna(backers_str):
        return []
    backers = backers_str.split(",")
    backers_locations = []
    for i in range(0, len(backers), 4):
        backer_info = {}
        if i < len(backers):
            backer_name = backers[i].strip()
            if backer_name:  # Check if the backer name is not empty
                backer_info["backer"] = backer_name
        if i + 2 < len(backers):
            location = backers[i + 2].strip()
            if location:  # Check if the location is not empty
                backer_info["location"] = location
        if backer_info:  # Only add if there's valid information
            backers_locations.append(backer_info)
    return backers_locations


# Create a new column for backers and locations
df["Backers_Locations"] = df["Backers"].apply(extract_backers_and_locations)

# Save the DataFrame back to a CSV file
df.to_csv("data_with_backers_locations_column3.csv", index=False)

# Optionally, display the DataFrame to verify the result
print(df[["Project Name", "Backers_Locations"]].head())
