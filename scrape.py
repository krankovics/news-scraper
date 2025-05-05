import os
import csv
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import openai
import smtplib
from email.message import EmailMessage

openai.api_key = os.getenv("OPENAI_API_KEY")

# ========== HÍRFORRÁSOK ==========
def fetch_agrarheute():
    url = "https://www.agrarheute.com/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    for item in soup.select("article.teaser"):
        title_elem = item.select_one(".teaser__title a")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link = "https://www.agrarheute.com" + title_elem.get("href")
        lead_elem = item.select_one(".teaser__intro")
        lead = lead_elem.get_text(strip=True) if lead_elem else ""
        articles.append({"title": title, "lead": lead, "link": link})
    return articles

def fetch_cenyrolnicze():
    url = "https://www.cenyrolnicze.pl/wiadomosci"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    for item in soup.select(".items-leading .catItemBody"):
        title_elem = item.select_one(".catItemTitle a")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link = title_elem.get("href")
        lead_elem = item.select_one(".catItemIntroText")
        lead = lead_elem.get_text(strip=True) if lead_elem else ""
        articles.append({"title": title, "lead": lead, "link": link})
    return articles

def fetch_farmer_pl():
    url = "https://www.farmer.pl/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    for item in soup.select(".listing .article-box"):
        title_elem = item.select_one(".article-title")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link = "https://www.farmer.pl" + title_elem.get("href")
        lead_elem = item.select_one(".article-lead")
        lead = lead_elem.get_text(strip=True) if lead_elem else ""
        articles.append({"title": title, "lead": lead, "link": link})
    return articles

def fetch_wiescirolnicze():
    url = "https://wiescirolnicze.pl/newsy/"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    articles = []
    for item in soup.select("div.td_module_10"):
        title_elem = item.select_one("h3.entry-title a")
        if not title_elem:
            continue
        title = title_elem.get_text(strip=True)
        link = title_elem.get("href")
        lead = ""
        articles.append({"title": title, "lead": lead, "link": link})
    return articles

# ========== FORDÍTÁS ==========
def translate_text(text):
    if not text:
        return ""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Te egy profi magyar fordító vagy."},
                {"role": "user", "content": f"Fordítsd le magyarra:\n\n{text}"}
            ],
            temperature=0.5
        )
        return response.choices[0].message["content"].strip()
    except Exception as e:
        print(f"Hiba a fordításnál: {e}")
        return text

# ========== EMAIL HTML-KÉNT ==========
def send_email(articles):
    email_address = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASS")
    email_to = os.getenv("EMAIL_TO")

    html_lines = []
    html_lines.append("<html><body>")
    html_lines.append("<h2>📰 Lefordított mezőgazdasági hírek</h2>")

    for article in articles:
        html_lines.append("<hr>")
        html_lines.append(f"<p><strong>{article['title']}</strong></p>")
        if article["lead"]:
            html_lines.append(f"<p><em>{article['lead']}</em></p>")
        html_lines.append(f"<p><a href='{article['link']}'>🔗 Eredeti cikk megtekintése</a></p>")

    html_lines.append("</body></html>")
    html_content = "\n".join(html_lines)

    msg = EmailMessage()
    msg["Subject"] = "📰 Lefordított mezőgazdasági hírek"
    msg["From"] = email_address
    msg["To"] = email_to
    msg.set_content("Ez a levél HTML formátumban készült. Kérlek, engedélyezd a megjelenítését.")
    msg.add_alternative(html_content, subtype="html")

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(email_address, email_password)
            smtp.send_message(msg)
        print(f"E-mail elküldve: {email_to}")
    except Exception as e:
        print(f"Hiba az email küldés során: {e}")

# ========== FŐ FOLYAMAT ==========
def main():
    all_articles = []
    all_articles += fetch_farmer_pl()
    all_articles += fetch_agrarheute()
    all_articles += fetch_cenyrolnicze()
    all_articles += fetch_wiescirolnicze()

    translated_articles = []
    for article in all_articles:
        print(f"Fordítás: {article['title']}")
        translated_title = translate_text(article["title"])
        translated_lead = translate_text(article["lead"])
        translated_articles.append({
            "title": translated_title,
            "lead": translated_lead,
            "link": article["link"]
        })

    send_email(translated_articles)
    print(f"{len(translated_articles)} hír lefordítva és elküldve.")

if __name__ == "__main__":
    main()
