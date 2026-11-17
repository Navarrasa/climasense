# Montagem no TinkerCAD Circuits

1. tinkercad.com → **Circuitos** → **Criar novo circuito**.
2. Arraste: Arduino Uno R3, 1 placa de ensaio (protoboard), 1 TMP36, 1 fotoresistor,
   3 potenciômetros, 1 botão, 3 LEDs (verde, amarelo, vermelho), 1 piezo,
   resistores: 1× 10 kΩ (LDR), 1× 10 kΩ (botão), 3× 220 Ω (LEDs).
3. Ligue o **5V** e o **GND** do Arduino nos trilhos + e − da protoboard.

| Componente | Ligação |
|---|---|
| TMP36 | pino esquerdo → 5V, central → **A0**, direito → GND (face plana para você) |
| Fotoresistor (LDR) | uma perna → 5V; outra perna → **A1** e → resistor 10 kΩ → GND |
| Potenciômetro "Qualidade do ar" | extremos → 5V e GND, cursor (meio) → **A2** |
| Potenciômetro "Umidade" | extremos → 5V e GND, cursor → **A3** |
| Potenciômetro "Pressão" | extremos → 5V e GND, cursor → **A4** |
| Botão "Pluviômetro" | um lado → 5V; outro lado → **D2** e → resistor 10 kΩ → GND |
| LED verde | anodo (perna dobrada) → 220 Ω → **D8**; catodo → GND |
| LED amarelo | anodo → 220 Ω → **D9**; catodo → GND |
| LED vermelho | anodo → 220 Ω → **D10**; catodo → GND |
| Piezo | + → **D11**; − → GND |

4. **Código** → troque "Blocos" por **Texto** → cole `estacao_tinkercad.ino`.
5. **Iniciar simulação** → abra o **Monitor serial**. Gire os potenciômetros,
   arraste o slider do TMP36/LDR e clique no botão para ver a saída JSON e os LEDs mudarem.

## Prints para o relatório
- Circuito montado (vista geral)
- Vista esquemática (botão "Vista esquemática" no canto superior direito)
- Monitor serial com as linhas JSON
- LED vermelho aceso + buzzer (forçar alerta: temperatura > 35 °C e umidade < 30 %)

## Justificativa (para o texto)
O TinkerCAD não oferece ESP32, DHT22, BMP280 nem MQ-135. Foram usados
equivalentes simulados (TMP36 e potenciômetros), mantendo a mesma lógica de
leitura, filtragem (média móvel de 5 amostras), validação por faixa e
alerta por álgebra booleana: **S = A·B + C + D**. Na transição para o
hardware real, só mudam as funções de leitura e a saída serial vira
publicação MQTT (ESP32 + Wi-Fi). No projeto, o script `simulador.py`
faz o papel do gateway MQTT, enviando ao backend leituras no mesmo formato JSON.
