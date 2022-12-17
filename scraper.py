import requests
from bs4 import BeautifulSoup
import pandas as pd

""" This script collects data about listings from Flatmates.com.au using Beautiful Soup library.
    This data is then stored into a pandas dataframe.
    The script only gets around 250 results.

"""


# Each property has an ID which is embedded as an href. 
def get_prop_id(soup):
    # find tags
    listings = soup.find_all("a",{"class" : "styles__contentBox___37_w9"})

    # initializing empty list to return
    prop_ids = []

    # Appending list with prop_IDs
    for i in range(0, len(listings)):

        # Slicing string to remove extra '\'
        prop_ids.append(listings[i]["href"][1:])
    return prop_ids

# Extracts listing address from all listings on a page
def get_listing_address(soup):
    # find tags
    listings = soup.find_all("p",{"class" : "styles__address___28Scu"})

    # initializing empty list to return
    suburb_list = []
    for i in range (0, len(listings)):

        # Splitting string to get only suburb name as city is set to Sydney
        # Appending to list
        if listings[i]:
            suburb_list.append(listings[i].text.rsplit(",",maxsplit=1)[0])
        else:
            suburb_list.append("N/A")
    return suburb_list

# Extracts listing rent from all listings on a page
def get_listing_price(soup):
    # find tags
    listings = soup.find_all("p",{"class" : "styles__price___3Jhqs"})

    # initializing empty lists to return
    price_list = []
    bills_inc = []

    for i in range(0, len(listings)):
        # Segregating listings that include bills in rent
        if listings[i]:
            if "inc. bills" in listings[i].text:
                bills_inc.append("Yes")
            else:
                bills_inc.append("No")

            # Splitting string to remove "/ week" as all prices are weekly
            split_one = listings[i].text.rsplit(" /",maxsplit=1)[0][1:]
            if "-" in listings[i].text:
                # Splitting string to get only lowest price for rooms available
                price_list.append((split_one.rsplit("-", maxsplit=1)[0]).strip())
            else:
                # Directly appending to price list one price is given
                price_list.append(split_one)
        else:
            price_list.append("N/A")
            bills_inc.append("N/A")

    return price_list, bills_inc

""" Extracts listing features :- 

    total population of the property, 
    number of beds, 
    number of bathrooms """

def get_prop_features(soup):
    # find tags (select is used as there is no specific identifier for features)
    listings = soup.select("div.styles__propertyFeature___uH480 p")

    # appending to list
    features_list = [listings[i].text if listings[i] else "N/A" for i in range(0, len(listings)) ]
    return features_list

# Extracts date of availability from all listings on a page
def get_avail_date(soup):
    # find tags
    listings = soup.find_all("p",{"class" : "styles__availability___UzGsZ"})

     # append to list
    avail_list = [listings[i].text if listings[i] else "N/A" for i in range(0, len(listings))]
    return avail_list


# Adds new rows to dataframe with every listing    
def populate_df(listing_df, row):

    # df.loc[] was used as df.append creates a new dataframe everytime (computationally expensive)
    listing_df.loc[len(listing_df.index)] = row
    return 






# Initializing empty dataframe
listing_df = pd.DataFrame({
"prop_ID":pd.Series(dtype="str"),
"rent_pw" : pd.Series(dtype="int"),
"suburb": pd.Series(dtype="str"),
"avail_date":pd.Series(dtype="str"),
"bills_inc" : pd.Series(dtype="str"),
"prop_pop" : pd.Series(dtype="int"),
"beds" : pd.Series(dtype="str"),
"baths" : pd.Series(dtype="str"),
})

# Setting page number
pg_no = 1

# While loop to get all posts from a page
while listing_df.shape[0] <= 250:  # Loop ends when df has 250 rows   
    MAIN_URL = f"https://flatmates.com.au/rooms/sydney?page={pg_no}"

    # Parse HTML using bs4 html parser    MAIN_URL = f"https://flatmates.com.au/rooms/sydney?page={pg_no}"

    # Send get requests to URL 
    pages = requests.get(MAIN_URL)

    # Parse HTML using bs4 html parser
    soup = BeautifulSoup(pages.text,"html.parser")

    # Finding tag that indicate end of results
    stop_mark = soup.find("div",{"class" : "styles__noResultsMainText___1Pd0K"})
    # Making stop conditon wiht a message
    if listing_df.shape[0] == 250:
        print("Reached maximum number of results")
        break

    # Making a stop condition when there are no more results
    elif stop_mark and stop_mark.text == "Sorry, we couldn't find any matches":
        print("End of Results")
        break

    # Calling functions and loading data into dataframe
    else:
        # Get property IDs
        prop_ids = get_prop_id(soup)
        # Get property features
        features = get_prop_features(soup)
        # Get rent and bills included
        price_list, bills_inc = get_listing_price(soup)
        # Get suburb
        suburb = get_listing_address(soup)
        # Get availabilty
        avail_date = get_avail_date(soup)
        
        n = 0 # Number of rows
        f = 0 # Indexing variable for features
        i = 0 # Indexing variable for other lists
        all_rows = {} # Dictionary with all rows for a page
        
        for id in prop_ids:
            row = {} # Create row dictionary per listing
            row["prop_ID"] = id
            row["rent_pw"] = price_list[i]
            row["suburb"] = suburb[i]
            row["avail_date"] = avail_date[i]
            row["bills_inc"] = bills_inc[i]


            # Features come in pairs of 3s
            row["beds"] = features[f]
            row["baths"] = features[f+1]
            row["prop_pop"] = features[f+2]
            all_rows[n] = row
            populate_df(listing_df, all_rows[n])
            
            
            f+=3 # Increasing by step size 3
            i+=1
            n+=1
        pg_no += 1
   