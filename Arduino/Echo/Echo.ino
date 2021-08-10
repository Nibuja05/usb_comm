/*
  Blink
  Turns on an LED on for one second, then off for one second, repeatedly.
 
  This example code is in the public domain.
 */
 
// Pin 13 has an LED connected on most Arduino boards.
// give it a name:
int incomingByte = 0;    // for incoming serial data
int led = 13;

void setup() {
    Serial.begin(9600);    // opens serial port, sets data rate to 9600 bps
    pinMode(led, OUTPUT);
}

void loop() {
  // send data only when you receive data:
  if (Serial.available() > 0) {
  
    // read the incoming byte:
    incomingByte = Serial.read();
  
    // say what you got:
    Serial.print((char)incomingByte);
    
    digitalWrite(led, HIGH);   // turn the LED on (HIGH is the voltage level)              // wait for a second
    digitalWrite(led, LOW);
  }
  
}
