#define MAX_STRING_LENGTH 10 // Maximum input string length
#define DEFAULT_QUERY_STRING_LENGTH 7 // Default length of the query part of the input strings

short pins[] = {A0};
char headers[4] = {'A', 'B', 'C', 'D'};
int used_channels{0};

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);
  for (int i=0; i<sizeof(pins); i++)
    pinMode(pins[i], INPUT);
}

void loop() {
  // put your main code here, to run repeatedly:
  if(Serial.available()>0)
  {
    char readString[MAX_STRING_LENGTH] = {""};
    readSerial(readString, MAX_STRING_LENGTH);
    String readSerialString{readString};
    if (readSerialString.equals("CH:AVA?\n"))
    {
      Serial.println(sizeof(pins)-1);
    }
    else if (readSerialString.substring(0, DEFAULT_QUERY_STRING_LENGTH).equals("CH:USE:"))
    {
        used_channels = readSerialString.substring(DEFAULT_QUERY_STRING_LENGTH).toInt();
        Serial.println(used_channels);
    }
    else if (readSerialString.equals("MEAS:ST\n"))
    {
      runMeasurement();
    }
  }
}

void readSerial(char* readString, int length)
{
  int i{0};
  
  while (Serial.available()>0 && i<length)
  {
    readString[i] = Serial.read();
    i++;
    delay(10);
  }
  // Serial.println(readString);
  return;
}

void runMeasurement()
{
  for (int i = 0; i<used_channels; i++)
  {
    Serial.print(headers[i]);
    float fieldValue{analogRead(pins[i]) * 5. / 1023. - 2.5};
    Serial.print(fieldValue);
    Serial.println();
    delay(1000);
  }
  return;
}
