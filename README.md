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

### 1. Sjekke nettverksstatus
```
nmcli device status
```

### 2. Sjekke om Wifi-kortet er aktivt
```
ip link show wlp2s0
```
Dette viser info om wifi-kortet, og om det er UP eller DOWN.
Om det var down prøvde jeg å aktivere det.

```
sudo ip link set wlp2s0 up
```


### 3. Sjekke Wifi-nettverk
Da sjekket jeg hvilke nettverk som var tilgjengelige.
```
nmcli device wifi list
```
Denne listen var helt tom, så da prøvde jeg å kjøre en rescan.
```
nmcli device wifi rescan
```


### 4. Starte nettverkstjenester på nytt
Det virket som om nettverkstjenestene hadde hengt seg opp. Da prøvde jeg å restarte tjenestene.
```
sudo systemctl restart NetworkManager
```


### 5. Reset av Wifi-driver
For å resette intel wifi-driveren:
```
sudo modprobe -r iwlwifi
sudo modprobe iwlwifi
```

