# Trellar

Prøveeksamen prosjekt på 2IMSTIT Elvebakken 2026. Ny og bedre trello copy hosta på linux.

## Plan:

En kopi av trello, bare litt bedre (forhåpentligvis).

Vil ha bedre customization og tasklists.

Skal være koblet opp på en database med brukere, prosjekter, og alt slikt.

Skal hostes på en linux laptop som kjører Ubuntu Server.

Deretter koble opp siden på cloudflare domenet mitt med en tunnel.

## Verktøy:

- Supabase
- Cloudflare
- Python Flask
- Ubuntu Server

## Ubuntu Server Oppsett:

Det jeg startet med å få gjort er å flashe ubuntu server på en gammel laptop.

Dette tok litt tid med formattering av usb disk osv, men fikk det fungerende etter en stund.

Jeg glemte å sette opp nett i opprettingen av systemet, så da manglet jeg nett. Etter timer med research og hjelp ifra chatgpt fikk jeg satt opp nettet slikt:


### 1. Sjekke at Wi-Fi-kortet blir oppdaget

Først sjekket jeg om Linux faktisk oppdaget nettverkskortet og hvilken driver som ble brukt.

```
lspci -nnk | grep -A3 -i network
```

Dette viste at maskinen brukte et **Intel WiFi Link 5100** nettverkskort med driveren `iwlwifi`.

---

### 2. Sjekke nettverksstatus

```
nmcli device status
```

Dette viser alle nettverksenheter og hvilken status de har. Her så jeg at Wi-Fi-enheten `wlp2s0` eksisterte, men ofte stod som `unavailable` eller `disconnected`.

---

### 3. Sjekke om Wifi-kortet er aktivt

```
ip link show wlp2s0
```

Dette viser info om wifi-kortet, og om det er `UP` eller `DOWN`.

Om det var `DOWN` prøvde jeg å aktivere det.

```
sudo ip link set wlp2s0 up
```

---

### 4. Sjekke om Wi-Fi er blokkert

Linux kan blokkere Wi-Fi via noe som heter **rfkill**. Derfor sjekket jeg om Wi-Fi var blokkert av systemet.

```
for f in /sys/class/rfkill/*; do echo "== $f =="; cat "$f/type" "$f/soft" "$f/hard" 2>/dev/null; done
```

Dette viste at Wi-Fi ikke var blokkert.

---

### 5. Sjekke Wifi-nettverk

Da sjekket jeg hvilke nettverk som var tilgjengelige.

```
nmcli device wifi list
```

Denne listen var helt tom, så da prøvde jeg å kjøre en rescan.

```
nmcli device wifi rescan
```

---

### 6. Sjekke nettverkskonfigurasjon (Netplan)

Ubuntu bruker **Netplan** for nettverkskonfigurasjon, så jeg sjekket hvilke konfigurasjonsfiler som fantes.

```
ls /etc/netplan
```

Deretter åpnet jeg konfigurasjonsfilene.

```
sudo cat /etc/netplan/*.yaml
```

Dette viste hvilke nettverk og innstillinger som var konfigurert.

---

### 7. Rette filrettigheter på Netplan-filer

Det kom en advarsel om at filrettighetene var feil, så jeg endret dem.

```
sudo chmod 600 /etc/netplan/*.yaml
```

---

### 8. Generere og bruke Netplan-konfigurasjonen på nytt

Etter endringene genererte jeg konfigurasjonen på nytt.

```
sudo netplan generate
sudo netplan apply
```

---

### 9. Starte nettverkstjenester på nytt

Det virket som om nettverkstjenestene hadde hengt seg opp. Da prøvde jeg å restarte tjenestene.

```
sudo systemctl restart NetworkManager
```

---

### 10. Reset av Wifi-driver

For å resette intel wifi-driveren:

```
sudo modprobe -r iwlwifi
sudo modprobe iwlwifi
```

Dette fjerner driveren helt og laster den inn på nytt.

---

### 11. Stoppe konflikter med wpa_supplicant

For å sikre at ingen andre prosesser kontrollerte Wi-Fi-kortet (det var noen andre prosesser som prøvde dette):

```
sudo pkill wpa_supplicant
```

---

### 12. Slå av og på Wifi

Til slutt viste det seg at Wi-Fi-radioen ikke skannet etter nettverk. Da løste jeg det ved å slå Wi-Fi av og på igjen.

```
nmcli radio wifi off
nmcli radio wifi on
```

Etter dette begynte systemet å oppdage trådløse nettverk igjen, og jeg fikk koblet serveren til internett.

---

### Målet
Målet med denne prosessen var å kunne få koblet meg opp til linuxen med ssh via macen senere.
Så ville jeg selvfølgelig kunne lukke linux-laptopen uten at jeg skulle bli koblet fra. Så da endret jeg **logind-konfigurasjonen** så lokk-lukking ble ignorert.
```
sudo nano /etc/systemd/logind.conf
HandleLidSwitch=ignore
sudo systemctl restart systemd-logind
```

---
