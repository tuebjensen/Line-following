/*
Based on isr.c from the WiringPi library, authored by Gordon Henderson
https://github.com/WiringPi/WiringPi/blob/master/examples/isr.c

Compile as follows:

    gcc -o run_encoder run_encoder.c -lwiringPi

*/

#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <stdlib.h>
#include <wiringPi.h>

// the event counter 
volatile int eventCounter = 0;

void ISR() {
   eventCounter++;
}

void writeHelp() {
    fprintf (stdout, "Usage: run_encoder [wiring-pi-pin]\n");
}

// -------------------------------------------------------------------------
// main
int main(int argvc, char *argv[]) {

  char *p;
  int num;

  errno = 0;
  long pinLong = strtol(argv[1], &p, 10);
  
  if (
    // this means that some error happened somewhere
    errno != 0 ||
    // check if it just a number, an not something like "12a\0" (here *p would be 'a' instead of '\0')
    *p != '\0'
    // We could also check if l > INT_MAX and l < INT_MIN, but it shouldn't matter,
    // since we will be passing in small numbers.
  ) {
    fprintf (stderr, "Error converting the argument to long: %s\n", strerror (errno));
    writeHelp();
    return 1;
  }

  int pin = pinLong;

  // sets up the wiringPi library
  if (wiringPiSetup () < 0) {
      fprintf (stderr, "Unable to setup wiringPi: %s\n", strerror (errno));
      return 1;
  }

  // setup interrupt on the given pin
  if (wiringPiISR (pin, INT_EDGE_FALLING, &myInterrupt) < 0) {
      fprintf(stderr, "Unable to setup ISR: %s\n", strerror (errno));
      return 1;
  }

  // display counter value every now and then
  while (1) {
    printf("%d\n", eventCounter);
    eventCounter = 0;
    delay(100);
  }

  return 0;
}
