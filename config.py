# config.py
# Database settings for MySQL running in XAMPP.
# These are the XAMPP default values.

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = ""        # XAMPP root user has no password by default
DB_NAME = "foodexa"

# Secret key used by Flask to keep session data safe
SECRET_KEY = "foodexa-secret-key"

# Restaurant contact details shown in the footer.
# These are SAMPLE values. Change them to the real details of the restaurant.
RESTAURANT_PHONE = "+977 98XXXXXXXX"
RESTAURANT_PHONE_2 = "056-XXXXXX"
RESTAURANT_EMAIL = "info@foodexa.com"
RESTAURANT_ADDRESS = "Bharatpur, Chitwan"

# Social media pages shown in the footer. Put the real page links here.
FACEBOOK_URL = "https://www.facebook.com/"
WHATSAPP_URL = "https://wa.me/"         # e.g. afnu page ya whats app ko url yeha repalce garni
INSTAGRAM_URL = "https://www.instagram.com/"
TIKTOK_URL = "https://www.tiktok.com/"
