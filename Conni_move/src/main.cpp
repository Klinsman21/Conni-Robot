// #include <Arduino.h>

// #define STEP_PIN 19  // GP2
// #define DIR_PIN  28  // GP3
// #define EN_PIN   2  // GP4 (opcional)

// void setup() {
//   pinMode(STEP_PIN, OUTPUT);
//   pinMode(DIR_PIN, OUTPUT);
//   pinMode(EN_PIN, OUTPUT);
//   digitalWrite(EN_PIN, LOW);  // Habilita o driver
// }

// void loop() {
//   digitalWrite(DIR_PIN, HIGH);  // Sentido horário
//   for (int i = 0; i < 200; i++) {  // 200 passos = 1 volta em motores 1.8°
//     digitalWrite(STEP_PIN, HIGH);
//     delayMicroseconds(500);
//     digitalWrite(STEP_PIN, LOW);
//     delayMicroseconds(500);
//   }
//   delay(1000);
// }

#include <Arduino.h>
#include <TMCStepper.h>
#include <AccelStepper.h>
#include "hardware/uart.h"
#include "pico/multicore.h"

#define UART_ID uart1
#define TX_PIN 8
#define RX_PIN 9
#define STEP_PINZ 19
#define DIR_PINZ 28
#define EN_PINZ 2
#define STEP_PINX 11
#define DIR_PINX 10
#define EN_PINX 12
#define STEP_PINY 6
#define DIR_PINY 5
#define EN_PINY 7
#define STEP_PINE 14
#define DIR_PINE 13
#define EN_PINE 15

enum
{
  ARM_LEFT,
  ARM_RIGHT,
};

class RP2040Serial : public Stream
{
public:
  void begin(unsigned long baudrate)
  {
    uart_init(UART_ID, baudrate);
    gpio_set_function(TX_PIN, GPIO_FUNC_UART);
    gpio_set_function(RX_PIN, GPIO_FUNC_UART);
  }

  virtual int available() override
  {
    return uart_is_readable(UART_ID);
  }

  virtual int read() override
  {
    if (available())
    {
      return uart_getc(UART_ID);
    }
    return -1;
  }

  virtual size_t write(uint8_t data) override
  {
    uart_putc(UART_ID, data);
    return 1;
  }

  virtual void flush() override {}
  virtual int peek() override { return -1; }
};
// Instâncias
RP2040Serial driverSerial;

TMC2209Stepper driverZ(&driverSerial, 0.11f, 0x01); // Motor Z
TMC2209Stepper driverX(&driverSerial, 0.11f, 0x00); // Motor X
TMC2209Stepper driverY(&driverSerial, 0.11f, 0x02); // Motor Y
TMC2209Stepper driverE(&driverSerial, 0.11f, 0x03); // Motor E
AccelStepper motorZ(AccelStepper::DRIVER, STEP_PINZ, DIR_PINZ);
AccelStepper motorX(AccelStepper::DRIVER, STEP_PINX, DIR_PINX);
AccelStepper motorY(AccelStepper::DRIVER, STEP_PINY, DIR_PINY);
AccelStepper motorE(AccelStepper::DRIVER, STEP_PINE, DIR_PINE);
bool stopMotorE_Flag = false;
bool stopLeft = false;
bool stopRight = false;
bool direction = false;
long last_print = 0;
uint16_t sgE, sgX;

void moveMotor(AccelStepper &motor, float distance, float speed, int direction)
{
  // Definir a velocidade máxima do motor
  motor.setMaxSpeed(speed);
  motor.setAcceleration(speed);

  // Calcular o número de passos que o motor precisa mover baseado na distância (em mm)
  // Aqui assumimos que o motor tem 200 passos por volta e 64 microsteps, o que dá 1.25 mm por passo
  float steps_per_mm = 200 * 64 / 68.96; // 1.25 mm por passo
  long steps_to_move = distance * steps_per_mm;

  // Ajusta a direção do movimento
  if (direction == -1)
  {
    steps_to_move = -steps_to_move;
  }
  motor.move(steps_to_move); // Move até a posição final calculada
}

void stopMotor(AccelStepper &motor)
{
  motor.setAcceleration(1000000); // Aceleração insana
  motor.setSpeed(0);              // Velocidade zero = para já
  motor.runSpeed();               // Aplica a velocidade imediatamente
  motor.stop();
}

void moveArm(int arm, int angle, int speed)
{
  if (arm == ARM_LEFT)
  {
    motorE.setMaxSpeed(speed);
    motorE.setAcceleration(speed);
    motorE.move(angle);
  }
  if (arm == ARM_RIGHT)
  {
    motorX.setMaxSpeed(speed);
    motorX.setAcceleration(speed);
    motorX.move(angle);
  }
}

int calibrateStepLeft = 0;
float stepsLeft = 0;
int calibrateStepRight = 0;
float stepsRight = 0;
void calibrateArmLeft()
{
  switch (calibrateStepLeft)
  {
  case 0:
    motorE.setCurrentPosition(0);
    motorE.setMaxSpeed(100000);
    motorE.setAcceleration(100000);
    motorE.move(200000);
    driverE.shaft(true);
    calibrateStepLeft++;
    break;

  case 1:
    if (sgE < 120 && stopLeft)
    {
      Serial.println("minimo");
      motorE.setCurrentPosition(0);
      stopMotor(motorE);
      stopLeft = false;
      calibrateStepLeft++;
      break;
    }
    break;
  case 2:
    driverE.shaft(false);
    motorE.setCurrentPosition(0);
    motorE.setMaxSpeed(100000);
    motorE.setAcceleration(100000);
    motorE.move(200000);
    calibrateStepLeft++;
    break;
  case 3:
    if (sgE < 120 && stopLeft)
    {
      stepsLeft = 200000 - motorE.distanceToGo();
      Serial.println("Passos totais");
      Serial.print(stepsLeft);
      motorE.setCurrentPosition(0);
      stopMotor(motorE);
      stopLeft = false;
      calibrateStepLeft++;
      break;
    }
    break;
  case 4:
    Serial.println("Centralizando");
    stepsLeft = stepsLeft / 1.25;
    Serial.println("Passos reversos");
    Serial.print(stepsLeft);
    driverE.shaft(true);
    motorE.setCurrentPosition(0);
    motorE.setMaxSpeed(100000);
    motorE.setAcceleration(100000);
    motorE.move(stepsLeft);
    calibrateStepLeft++;
    break;
  }
}

void calibrateArmRight()
{
  switch (calibrateStepRight)
  {
  case 0:
    motorX.setCurrentPosition(0);
    motorX.setMaxSpeed(100000);
    motorX.setAcceleration(100000);
    driverX.shaft(false);
    motorX.move(200000);
    calibrateStepRight++;
    break;

  case 1:
    if (sgX < 120 && stopRight)
    {
      Serial.println("minimo");
      driverX.shaft(true);
      motorX.setCurrentPosition(0);
      stopMotor(motorX);
      stopRight = false;
      calibrateStepRight++;
      break;
    }
    break;
  case 2:
    motorX.setCurrentPosition(0);
    motorX.setMaxSpeed(100000);
    motorX.setAcceleration(100000);
    motorX.move(200000);
    calibrateStepRight++;
    break;
  case 3:
    if (sgX < 120 && stopRight)
    {
      driverX.shaft(false);
      stepsRight = 200000 - motorX.distanceToGo();
      Serial.println("Passos totais");
      Serial.print(stepsRight);
      motorX.setCurrentPosition(0);
      stopMotor(motorX);
      stopRight = false;
      calibrateStepRight++;
      break;
    }
    break;
  case 4:
    Serial.println("Centralizando");
    stepsRight = stepsRight / 1.25;
    Serial.println("Passos reversos");
    Serial.print(stepsRight);
    motorX.setCurrentPosition(0);
    motorX.setMaxSpeed(100000);
    motorX.setAcceleration(100000);
    motorX.move(stepsRight);
    calibrateStepRight++;
    break;
  }
}

void second_core_main() {
  while (true) {
      // código que roda no segundo core
      Serial.println("Core 1 rodando\n");
      delay(1000);
  }
}

void setup()
{
  Serial.begin(115200);
  driverSerial.begin(115200);

  pinMode(EN_PINZ, OUTPUT);
  digitalWrite(EN_PINZ, LOW);
  pinMode(EN_PINX, OUTPUT);
  digitalWrite(EN_PINX, LOW);
  pinMode(EN_PINY, OUTPUT);
  digitalWrite(EN_PINY, LOW);
  pinMode(EN_PINE, OUTPUT);
  digitalWrite(EN_PINE, LOW);

  driverZ.begin();
  driverZ.rms_current(1000);
  driverZ.microsteps(64);
  driverZ.toff(4);
  driverX.begin();
  driverX.rms_current(500);
  driverX.microsteps(64);
  driverX.toff(4);
  driverY.begin();
  driverY.rms_current(1000);
  driverY.microsteps(64);
  driverY.toff(4);
  driverE.begin();
  driverE.rms_current(500);
  driverE.microsteps(64);
  driverE.toff(4);

#define STALL_VALUE 63 // ajuste conforme o seu motor

  driverE.TCOOLTHRS(0xFFFFF); // habilita stallguard sempre
  driverE.semin(5);           // ativa smart current control (SmartGuard)
  driverE.semax(2);           // intervalo de SmartGuard
  driverE.sedn(0b01);         // decremento de current
  driverE.SGTHRS(STALL_VALUE); // sensibilidade do StallGuard (-64 a +63)
  driverX.TCOOLTHRS(0xFFFFF); // habilita stallguard sempre
  driverX.semin(5);           // ativa smart current control (SmartGuard)
  driverX.semax(2);           // intervalo de SmartGuard
  driverX.sedn(0b01);         // decremento de current
  driverX.SGTHRS(STALL_VALUE); // sensibilidade do StallGuard (-64 a +63)
  delay(5000);
  multicore_launch_core1(second_core_main);
}

void loop()
{
  //calibrateArmLeft();
  //calibrateArmRight();
  if (motorZ.distanceToGo() != 0)
  {
    motorZ.run();
  }
  if (motorX.distanceToGo() != 0)
  {
    motorX.run();
  }
  if (motorY.distanceToGo() != 0)
  {
    motorY.run();
  }
  if (motorE.distanceToGo() != 0)
  {
    motorE.run();
  }

  if (millis() - last_print >= 15)
  {
    last_print = millis(); // ← importante!
    sgE = driverE.SG_RESULT();
    sgX = driverX.SG_RESULT();
    
    if (sgE > 150)
    {
      stopLeft = true;
    }
    if (sgX > 150)
    {
      stopRight = true;
    }
  }
}