
#include "StringSplitter.h"

int logbit = 0, logging = 0;
String incomingString;
int dataArray[15];

void setup() {
	Serial.begin(115200);
}

void decode_input(String iB) {
  StringSplitter *splitter = new StringSplitter(iB, ';', 20);
  int itemCount = splitter->getItemCount();
  for(int i = 0; i < itemCount; i++){
    dataArray[i] = splitter->getItemAtIndex(i).toInt();
  }
}

void move_motors() {
//  DataArray is an array in the format as you had before,
//  but with an extra number at the end representing logging.
//  eg. 1;0;0;0;2;................;1 <--- ignore last number

//  Put existing code here for moving motors using CAN
}

String get_motor_data() {
  String final_data;
//  Read data from motors into final_data string
//  return final_data;
  return "got motor data";
}

void loop() {
  if (Serial.available()) {
    incomingString = Serial.readString();
    Serial.print("USB received:    ");
    Serial.println(incomingString);
    decode_input(incomingString);
    logbit = dataArray[14];
//    Serial.println(logbit);
    if (!logging) {
      move_motors();
      Serial.println();
      if (logbit) {logging = 1;}
    } else {
      if (!logbit) {logging = 0;}
      move_motors();
      Serial.println(get_motor_data());
    }
    Serial.flush();
  }
}
