from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
from player import Player
from enum import Enum
from prettytable import PrettyTable

class StatType(Enum):
    APPEARANCES = "appearances"
    TACKLE = "total_tackle"


class PremierLeagueScraper:
    BASE_URL = "https://www.premierleague.com/stats/top/players/"
    STAT_URL_MAPPING = {
        StatType.APPEARANCES: "appearances?se=-1",
        StatType.TACKLE: "total_tackle?se=-1"
    }
    STAT_CLASS_MAPPING = 'stats-table__main-stat'

    def __init__(self, stat_type, num_pages=3, headless=True):
        self.stat_type = stat_type
        self.num_pages = num_pages
        self.headless = headless
        self.driver = self._initialize_driver()

    def _initialize_driver(self):
        options = Options()
        options.add_argument('--no-sandbox')
        if self.headless:
            options.add_argument('--headless')
        return webdriver.Chrome(options=options)

    def handle_cookies(self):
        try:
            manage_cookies_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "onetrust-pc-btn-handler"))
            )
            manage_cookies_button.click()

            accept_recommended_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "accept-recommended-btn-handler"))
            )
            accept_recommended_button.click()

            time.sleep(10)
        except:
            pass

    def get_stat_url(self):
        return self.BASE_URL + self.STAT_URL_MAPPING[self.stat_type]

    def get_stat_class(self):
        return self.STAT_CLASS_MAPPING

    def scrape_table(self, html_content):
        players = []
        soup = BeautifulSoup(html_content, "html.parser")

        table_body = soup.find('tbody', class_='stats-table__container')
        if table_body:
            rows = table_body.find_all('tr', class_='table__row')

            for row in rows:
                rank = row.find('td', class_='stats-table__rank').text.strip()

                player_name_elem = row.find('a', class_='playerName')
                player_name = player_name_elem.text.strip()
                player_link = player_name_elem['href']
                if player_link.startswith('//'):
                    player_link = player_link[2:]

                nationality_elem = row.find('span', class_='playerCountry')
                nationality = nationality_elem.text.strip() if nationality_elem else 'Unknown'

                stat = row.find('td', class_=self.get_stat_class()).text.strip()

                club_elem = row.find('a', class_='stats-table__cell-icon-align')
                club = club_elem.text.strip() if club_elem else 'Retired/Unknown'

                player = Player(rank, player_name, nationality, club, stat, player_link)
                players.append(player)

        return players

    def click_next_button(self):
        next_button = WebDriverWait(self.driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".paginationNextContainer"))
        )
        next_button.click()
        time.sleep(5)

    def scrape(self):
        url = self.get_stat_url()
        players_data = []

        try:
            self.driver.get(url)
            self.handle_cookies()

            for _ in range(self.num_pages):
                html_content = self.driver.page_source
                players = self.scrape_table(html_content)
                players_data.extend(players)
                self.click_next_button()
        finally:
            self.driver.quit()

        return players_data
    
    def print_players_table(self):
        players = self.scrape()
        table = PrettyTable()
        table.field_names = ["Rank", "Player Name", "Nationality", "Club", "Stat", "Player Link"]
        for player in players:
            table.add_row([player.rank, player.name, player.nationality, player.club, player.stat, player.player_link])
        print(f"Top {self.num_pages * 10} {self.stat_type.value} in the Premier League")
        print(table)

if __name__ == "__main__":
    stat_type = StatType.TACKLE
    num_pages = 3
    scraper = PremierLeagueScraper(stat_type, num_pages=num_pages, headless=True)
    scraper.print_players_table()