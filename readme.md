# AIoT & ROBO LAB 2.0 - Kävijäseuranta ja ennustejärjestelmä

Tämä on alkuperäisestä projektista erillinen 2.0-versio. Se seuraa laboratorion kävijämääriä MQTT-protokollalla, tallentaa havainnot MongoDB-pilvitietokantaan ja visualisoi ne Streamlit-dashboardilla.

## Ominaisuudet

- Reaaliaikainen MQTT-pohjainen datankeruu.
- MongoDB-pilvitallennus `occupancy`-kokoelmaan.
- Historialliseen dataan perustuva 24 tunnin ennuste ja viikoittainen lämpökartta.
- MongoDB-indeksit aikaleimalle sekä laite- ja aikaleimayhdistelmälle.

## Asennus ja käyttö

1. Luo ja aktivoi virtuaaliympäristö:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

   Windowsissa aktivointi on `venv\Scripts\activate`.

2. Asenna riippuvuudet:

   ```bash
   pip install -r requirements.txt
   ```

3. Luo asetustiedosto ja täytä sen arvot:

   ```bash
   cp .env.example .env
   ```

   `.env` sisältää seuraavat asetukset:

   ```env
   MQTT_USER=kayttajanimi
   MQTT_PASS=salasana
   MQTT_HOST=broker.osoite.com
   MQTT_PORT=1883
   MQTT_TOPIC=labra/occupancy

   MONGODB_URI=mongodb+srv://kayttaja:salasana@klusteri.mongodb.net/?retryWrites=true&w=majority
   MONGODB_DATABASE=aiot_occupancy
   MONGODB_COLLECTION=occupancy
   ```

   MongoDB Atlasissa lisää käyttämäsi IP-osoite Network Access -listaan ja anna tietokantakäyttäjälle luku- ja kirjoitusoikeus.

4. Käynnistä datankeruu. Ensimmäinen käynnistys testaa MongoDB-yhteyden ja luo indeksit automaattisesti:

   ```bash
   python src/mqtt_collector.py
   ```

5. Käynnistä dashboard toisessa terminaalissa:

   ```bash
   streamlit run src/dashboard.py
   ```

## Mallin tulkinta

- Harmaa katkoviiva: historiallinen keskiarvo.
- Turkoosi viiva: tämän päivän toteuma.
- Lämpökartta: viikon ruuhkaisimmat päivät ja kellonajat.
