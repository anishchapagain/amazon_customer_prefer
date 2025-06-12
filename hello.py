import requests
import json
import time
import re

BASE_URL = "https://read.amazon.com/sample/rec/"
BASE_QUERY = "?max=0&locale=en_US" #24 or 0
DATASET_IDS = []
DATASET_URLS = []
ASIN_REGEX = r"^[A-Z0-9]{10}$"

def fetch_book_data(book_id):
    url = BASE_URL+book_id+BASE_QUERY
    DATASET_URLS.append(url)
    print(f"Fetching data__ URL: {url}")

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if len(data.get("recsSamplesInfo"))>0:
            return data #["recsSamplesInfo"]
        else:
            print("No book data found in the response.")
            return None
    else:
        print(f"Error fetching data: {response.status_code}")
        return None

def collect_book_data(book_id):
    book_data = fetch_book_data(book_id)
    time.sleep(2)
    book_details = {}
    book_samples = book_data.get("recsSamplesInfo", [])
    book_asins = book_data.get("recommendedAsins", [])
    book_widgets = book_data.get("widgetTitle", "")

    if book_data:
        with open("book_data.json", "w") as file:
            json.dump(book_data, file, indent=4)

        # print("Book data collected successfully")
        print(f"-- Found Processing book for {book_id} - {len(book_asins)}  - {book_widgets}")
        print(book_asins)
        
        for book in book_samples:
            books = {}
            asin = book.get("asin")
            if not re.match(ASIN_REGEX, asin):
                print("ASIN is empty, skipping this book.")
                continue
            # DATASET_IDS.append(asin)
           
            books["title"] = book.get("title", "")
            if len(book["authorInfoList"])> 0:
                books["total_authors"] = len(book["authorInfoList"])
                # print(f"Total authors: {book_details['total_authors']}")
                for i,author_info in enumerate(book["authorInfoList"]):
                    i+= 1
                    books[f"author_{i}"] = author_info["authorName"]
                    books[f"authorDetailPageUrl_{i}"] = author_info.get("authorDetailPageUrl", "")
            else:
                books["total_authors"] = 0
                books["author_1"] = "N/A"
                books["authorDetailPageUrl_1"] = "N/A"

            books["asin"] = asin
            books["imageUrl"] = book.get("coverImage","")
            books["rating"] = book.get("averageRating", 0)
            books["numberOfReviews"] = book.get("numberOfReviews", "")
            books["reviewsUrl"] = book.get("customerReviewsUrl", "")
            books["price"] = book.get("priceDisplayString", "").replace("$", "")
            
            
            if asin not in book_details.keys() and re.match(ASIN_REGEX, asin):
                global DATASET_IDS
                DATASET_IDS.append(asin)
                book_details[asin] = books
            else:
                print(f" *** DUPLICATE: Book with ASIN {asin} already exists in the dataset.")
                
    else:
        print("Failed to collect book data.")
        time.sleep(1)
    return book_details
    
def collect_data(book_id):
    return collect_book_data(book_id)
    

def main():
    datasets = dict()
    datasets_ids = {"asins": []}
    datasets_urls = {"urls": []}

    print("Hello from amazon-books!")
    
    book_id_default = ""
    default_id= input("Enter a default book ID (or type 'exit' to stop): ")
    
    if default_id.lower()=='exit':
        print("Exiting the script.")
        return
    
    elif re.match(ASIN_REGEX, default_id):
        book_id_default = default_id.strip()  # 1098166302
        if not re.match(ASIN_REGEX, book_id_default): 
            print("Invalid ASIN format. Please enter a valid ASIN.")
            return
        else:
            DATASET_IDS.append(book_id_default)
            datasets.update(collect_data(book_id_default))
            print("Book data collection completed.")

    else:
        print("Please try to execute the code again")

    step = 1
    if not len(DATASET_IDS):
        print("No book IDs found.")
    else:    
        for book_id in list(set(DATASET_IDS)):
            datasets.update(collect_data(book_id))
            print(f" -- Dataset updated with {len(list(datasets.keys()))} books from {book_id} - {len(set(DATASET_IDS))}.")
            total_ids = len(DATASET_IDS)
            if step % 5 == 0:
                print(f"Processed {step} times already, sleeping for 5 seconds to avoid rate limiting. {total_ids} - {len(datasets.keys())}")
                time.sleep(5)
            step += 1

            if len(list(datasets.keys())) > 1000:
                print(f"Total books collected: {len(datasets.keys())}")
                print("STOPPIng.....")
                break


    with open("dataset_final.json", "w") as file:
        json.dump(datasets, file, indent=4)

    with open("data_ids.json", "w") as file:
        datasets_ids["asins"] = list(set(DATASET_IDS))
        json.dump(datasets_ids, file, indent=4)

    with open("data_urls.json", "w") as file:
       datasets_urls["urls"]=list(set(DATASET_URLS))
       json.dump(datasets_urls, file, indent=4)

    print("Total books processed:", len(datasets.keys()))

if __name__ == "__main__":
    main()