import os
from dotenv import load_dotenv
from amadeus import Client, ResponseError

# Load .env file - try multiple paths
load_dotenv('/app/.env')
if not os.getenv('AMADEUS_API_KEY'):
    load_dotenv('.env')
if not os.getenv('AMADEUS_API_KEY'):
    load_dotenv('../.env')

def get_hotel_list():
    env = os.getenv('AMADEUS_ENV', 'test') or 'test'
    hostname = 'production' if env.lower() == 'production' else 'test'
    amadeus = Client(
        client_id=os.getenv('AMADEUS_API_KEY'),
        client_secret=os.getenv('AMADEUS_API_SECRET'),
        hostname=hostname,
    )

    try:
        print(f"--- {env.upper()} ortaminda test ediliyor ---")
        print("1. Baglanti testi (IST havalimani)...")
        amadeus.reference_data.locations.get(keyword='IST', subType="AIRPORT")
        print("   [OK] Baglanti basarili.")

        print("2. Otel listesi testi (Paris - PAR)...")
        hotels_response = amadeus.reference_data.locations.hotels.by_city.get(cityCode='PAR')
        if hotels_response.data:
            print(f"   [OK] {len(hotels_response.data)} adet otel bulundu.")
            first = hotels_response.data[0]
            print(f"   Ornek Otel ID: {first.get('hotelId')}")
        else:
            print("   [UYARI] Istek basarili ama otel listesi bos.")
    except ResponseError as error:
        print("\n!!! Bir hata olustu !!!")
        print(f"Status Code: {error.response.status_code}")
        print(f"Hata Kodu: {error.code}")
        print(f"Hata Mesaji: {error.response.body}")
        if error.response.status_code == 401:
            print(" -> Ipucu: API key/secret yanlis veya ortam uyusmuyor.")
        elif error.response.status_code == 403:
            print(" -> Ipucu: Bu endpoint icin yetkiniz yok.")
        elif error.response.status_code == 400:
            print(" -> Ipucu: Parametreler hatali.")
        elif error.response.status_code == 500:
            print(" -> Ipucu: Amadeus sunuculari sorunlu olabilir.")

if __name__ == '__main__':
    get_hotel_list()

