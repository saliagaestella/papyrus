import requests
from bs4 import BeautifulSoup
from datetime import date

def scrape_disposition_text(url):
    """Scrapes the text content from a disposition's HTML page."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")

        # The text is within the <div class="disposicion">
        disposicion_div = soup.find("div", class_="disposicion")
        if not disposicion_div:
            print(f"Could not find <div class='disposicion'> in {url}")
            return None

        # Extract all text from <p> tags within the disposicion div
        paragraphs = disposicion_div.find_all("p")
        text_content = "\n".join(p.get_text(strip=True) for p in paragraphs) #Join all paragraphs with a new line.

        return text_content

    except requests.exceptions.RequestException as e:
        print(f"Error during request for {url}: {e}")
        return None
    except Exception as e:
        print(f"Error processing {url}: {e}")
        return None

def scrape_bocyl_disposiciones_generales(date_str=None):
    """
    Scrapes the "Disposiciones Generales" section from the Boletín Oficial de Castilla y León (BOCYL)
    for a given date.

    Args:
        date_str (str, optional): The date to scrape in "dd/mm/yyyy" format.  If None, defaults to today's date.

    Returns:
        list: A list of dictionaries, where each dictionary represents a disposición general
              and contains the 'title' and 'link' to the full text.  Returns an empty list if
              no disposiciones generales are found or if an error occurs.
    """

    if date_str is None:
        today = date.today()
        date_str = today.strftime("%d/%m/%Y")

    url = f"https://bocyl.jcyl.es/boletin.do?fechaBoletin={date_str}"

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.content, "html.parser")

        # Find the "Disposiciones Generales" section using the id and class of the heading.
        seccion_heading = soup.find("h4", {"class": "encabezado4_sinlinea", "id": "I.A._DISPOSICIONES_GENERALES"})

        if not seccion_heading:
            print("No 'Disposiciones Generales' section found on the page.")
            return []

        # Find all the following <h5 class="encabezado6"> tags until the next h4 tag
        disposiciones = []
        for element in seccion_heading.find_next_siblings():
            if element.name == "h4":  # Stop when you reach the next h4 (section)
                break
            if element.name == "h5" and element.has_attr("class") and element["class"][0] == "encabezado6":
                # Extract title from the following <p> tag
                p_tag = element.find_next_sibling("p")
                if p_tag:
                    title = p_tag.get_text(strip=True)

                    # Extract the link from the <a> tag inside the <ul> with class "descargaBoletin"
                    ul_tag = p_tag.find_next_sibling("ul", {"class": "descargaBoletin"})
                    if ul_tag:
                        # Look for the link to the HTML version.
                        a_tag = ul_tag.find("a", href=True, title=lambda t: t and "html" in t.lower()) #Find the <a> tag whose title contains "html"
                        if a_tag:
                            link = a_tag["href"]
                            # Make the link absolute if it's relative
                            if not link.startswith("http"):
                                link = f"https://bocyl.jcyl.es/{link}"

                            disposiciones.append({"title": title, "link": link})

        return disposiciones

    except requests.exceptions.RequestException as e:
        print(f"Error during request: {e}")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []


if __name__ == "__main__":
    # Example usage:
    today = date.today()
    date_str = today.strftime("%d/%m/%Y")  # Date in DD/MM/YYYY format
    disposiciones = scrape_bocyl_disposiciones_generales(date_str)

    all_texts = [] #List to store all text content from disposiciones.

    if disposiciones:
        print(f"Disposiciones Generales for {date_str}:\n")
        for disp in disposiciones:
            print(f"- {disp['title']}")
            print(f"  Link: {disp['link']}")
            print("-" * 20)

            # Scrape and store the text content:
            text = scrape_disposition_text(disp['link'])
            if text:
                all_texts.append(text)
            else:
                all_texts.append(f"Error scraping text from {disp['link']}") #Append error message if text couldn't be scraped.

        # Display all the extracted text content:
        print("\n--- Extracted Text Content ---\n")
        for i, text in enumerate(all_texts):
            print(f"Disposition {i+1}:\n{text}\n{'-'*40}")

    else:
        print(f"No Disposiciones Generales found for {date_str}.")