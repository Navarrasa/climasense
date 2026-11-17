/*
 * Estacao Meteorologica Inteligente - firmware para simulacao no TinkerCAD
 * Placa: Arduino Uno R3 (o TinkerCAD nao possui ESP32; a logica e a mesma)
 *
 * Sensores (equivalentes disponiveis no TinkerCAD):
 *   A0 - TMP36 ............... temperatura (substitui DHT22/BMP280)
 *   A1 - Fotoresistor (LDR) .. luminosidade (divisor com resistor 10k)
 *   A2 - Potenciometro ....... qualidade do ar (simula MQ-135)
 *   A3 - Potenciometro ....... umidade relativa (simula DHT22)
 *   A4 - Potenciometro ....... pressao atmosferica (simula BMP280)
 *   D2 - Botao (pull-down) ... pluviometro de bascula (cada clique = 0,2 mm)
 * Atuadores:
 *   D8 LED verde (normal) | D9 LED amarelo (atencao) | D10 LED vermelho (alerta)
 *   D11 Buzzer piezo (alerta)
 *
 * Saida: uma linha JSON por leitura no Monitor Serial (9600 baud).
 * Na versao com ESP32 real, essa mesma string seria publicada via MQTT
 * no topico "estacao/01/leituras".
 */

const int PIN_TEMP = A0, PIN_LDR = A1, PIN_AR = A2, PIN_UMID = A3, PIN_PRESS = A4;
const int PIN_CHUVA = 2;
const int LED_OK = 8, LED_ATENCAO = 9, LED_ALERTA = 10, BUZZER = 11;

const float MM_POR_BASCULA = 0.2;
const unsigned long INTERVALO_MS = 2000;
const int N_AMOSTRAS = 5;  // media movel simples (filtro)

volatile unsigned int basculas = 0;
unsigned long ultimoPulso = 0;
unsigned long ultimaLeitura = 0;

void contaChuva() {
  // debounce por software: ignora pulsos com menos de 200 ms
  unsigned long agora = millis();
  if (agora - ultimoPulso > 200) { basculas++; ultimoPulso = agora; }
}

int lerMedia(int pino) {
  long soma = 0;
  for (int i = 0; i < N_AMOSTRAS; i++) { soma += analogRead(pino); delay(5); }
  return soma / N_AMOSTRAS;
}

// Validacao por logica proposicional: valido = (min <= v) AND (v <= max)
bool valido(float v, float vmin, float vmax) { return (v >= vmin) && (v <= vmax); }

void setup() {
  Serial.begin(9600);
  pinMode(PIN_CHUVA, INPUT);
  pinMode(LED_OK, OUTPUT); pinMode(LED_ATENCAO, OUTPUT);
  pinMode(LED_ALERTA, OUTPUT); pinMode(BUZZER, OUTPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_CHUVA), contaChuva, RISING);
}

void loop() {
  if (millis() - ultimaLeitura < INTERVALO_MS) return;
  ultimaLeitura = millis();

  // --- Leitura e conversao ---
  float tensao = lerMedia(PIN_TEMP) * (5.0 / 1023.0);
  float temperatura = (tensao - 0.5) * 100.0;              // TMP36: 10 mV/C, offset 0,5 V
  float luminosidade = lerMedia(PIN_LDR) / 1023.0 * 100.0; // % de luz
  int qualidadeAr = map(lerMedia(PIN_AR), 0, 1023, 0, 500); // indice AQI simulado
  float umidade = lerMedia(PIN_UMID) / 1023.0 * 100.0;      // %
  float pressao = 950.0 + lerMedia(PIN_PRESS) / 1023.0 * 100.0; // 950..1050 hPa
  float chuva = basculas * MM_POR_BASCULA;                  // mm acumulados

  // --- Validacao ---
  bool tOk = valido(temperatura, -10, 60);
  bool uOk = valido(umidade, 0, 100);
  bool pOk = valido(pressao, 900, 1100);
  bool dadosOk = tOk && uOk && pOk;

  // --- Algebra de Boole para o nivel de alerta ---
  // A = calor extremo, B = ar seco, C = ar poluido, D = chuva forte
  bool A = temperatura > 35;
  bool B = umidade < 30;
  bool C = qualidadeAr > 150;
  bool D = chuva > 10;
  bool alerta  = (A && B) || C || D;          // S = A.B + C + D
  bool atencao = !alerta && (A || B || qualidadeAr > 100);

  digitalWrite(LED_OK, !alerta && !atencao);
  digitalWrite(LED_ATENCAO, atencao);
  digitalWrite(LED_ALERTA, alerta);
  if (alerta) tone(BUZZER, 1000, 200); else noTone(BUZZER);

  // --- Saida JSON (mesmo formato aceito pela API) ---
  Serial.print("{\"estacao_id\":1");
  Serial.print(",\"temperatura\":");  Serial.print(temperatura, 1);
  Serial.print(",\"umidade\":");      Serial.print(umidade, 1);
  Serial.print(",\"pressao\":");      Serial.print(pressao, 1);
  Serial.print(",\"qualidade_ar\":"); Serial.print(qualidadeAr);
  Serial.print(",\"luminosidade\":"); Serial.print(luminosidade, 1);
  Serial.print(",\"chuva_mm\":");     Serial.print(chuva, 1);
  Serial.print(",\"valido\":");       Serial.print(dadosOk ? "true" : "false");
  Serial.println("}");
}
