
#include "StringSplitter.h"

void setup() {
	Serial.begin(11500);
	HWSERIAL.begin(11500);
}

void decode_input(String iB) {
  StringSplitter *splitter = new StringSplitter(iB, ';', 14);
  int itemCount = splitter->getItemCount();
  int[14] items;
  for(int i = 0; i < itemCount; i++){
    items[i] = splitter->getItemAtIndex(i);
  }
}

void move_motors(String iB) {
  
}

void loop() {
  String incomingString;
        
  if (Serial.available() > 0) {
    incomingString = Serial.read();
    Serial.print("USB received: ");
    Serial.println(incomingString);
    move_motors(incomingString);
    Serial.flush();
  }
}
