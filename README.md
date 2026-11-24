# PocketLab

Canivete de laboratorio 100% Termux, sem hardware externo.
Interface com rich, banco SQLite, export JSON/CSV, gerador NEC e etiquetas de lab.

Escopo: automacao, logging e as funcoes que o celular executa sozinho.
Uso em equipamentos proprios ou com autorizacao por escrito.

## O que funciona de verdade

| Ferramenta | Roda no celular puro? | Observacao |
|---|---|---|
| IR transmitir (raw + NEC) | Sim, se houver blaster nativo | via Termux:API |
| IR capturar | Nao | exige receptor externo |
| Scan da rede local | Sim (sem root) | TCP connect, sua rede |
| Etiquetas de lab | Sim | devices + associacao de capturas |
| Historico / export | Sim | SQLite + JSON/CSV |
| NFC / BLE / WiFi analyzer | Via app | o PocketLab abre os apps |
| Sub-GHz 433/868 | Nao | radio nao existe no celular |
| RFID 125 kHz | Nao | antena LF nao existe |
| GPIO / UART / SPI | Nao | sem pinos expostos |

## Instalacao (Termux)

    pkg update -y
    pkg install python termux-api git -y
    termux-setup-storage
    pip install rich
    git clone https://github.com/Kaike-Pasternak-dev/poketlab.git
    cd poketlab
    python -m pocketlab

Como comando instalado:

    pip install .
    pocketlab

## Uso

Menu numerado. Digite o numero da ferramenta e Enter.

- 1 lista as frequencias do blaster IR
- 2 transmite um pattern IR raw (microssegundos)
- 3 gera pattern NEC a partir de address/command (padrao ou extendido)
- 4 varre a sua rede local por hosts/portas comuns
- 5 abre NFC Tools / MCT / nRF Connect / WiFi Analyzer
- 6 etiquetas de lab: cadastra devices e associa capturas
- 7 historico de capturas
- 8 exporta JSON + CSV
- 9 diagnostico do que o aparelho suporta
- s sobre / limites de hardware

## Gerador NEC

Opcao 3 monta o pattern NEC completo (leader + 32 bits + stop) a partir de
address e command em hex. NEC padrao usa address 8 bits com inverso;
NEC extendido usa address 16 bits. Carrier 38 kHz. Se o aparelho nao tiver
blaster, o pattern e salvo no banco mesmo assim.

## Etiquetas de lab

Opcao 6 cadastra devices (nome, categoria, local, notas) e associa capturas
a eles. Util pra registrar qual aparelho e qual e agrupar os sinais/logs
de cada um. Tudo no SQLite local.

## Limites de hardware

O celular nao tem radio Sub-GHz, antena 125 kHz, receptor IR nem GPIO.
Para essas funcoes e preciso hardware externo (ESP32 + CC1101, RDM6300, RTL-SDR).
NFC e monitor mode WiFi dependem de app/kernel especificos.

## Legalidade (Brasil)

Lei 12.737/2012, Marco Civil 12.965/2014, LGPD 13.709/2018.
Transmitir fora dos limites Anatel e infração. Pentest exige autorizacao por escrito.

## Licenca

MIT - veja LICENSE.
