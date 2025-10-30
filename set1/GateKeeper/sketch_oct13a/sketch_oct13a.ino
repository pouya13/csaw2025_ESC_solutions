// Arduino UNO (ATmega328P)
// D8 (ICP1) measures RISING -> FALLING using Timer1 Input Capture.
// Robust to overflow race: builds a 32-bit "extended timestamp" at each capture.
// Prints one line per measurement: microseconds with 2 decimals.

volatile uint32_t ovfCount = 0;

volatile uint32_t startStamp = 0;  // 32-bit extended tick timestamp
volatile uint32_t endStamp   = 0;
volatile bool haveMeasurement = false;
volatile bool waitingRising  = true;

static inline uint32_t make_extended_stamp(uint16_t icr, uint8_t tifr_snapshot, uint32_t ovf_snapshot) {
  // If an overflow occurred *right after* the capture (TOV1 set but OVF ISR not run yet),
  // and the captured count is in the "after-overflow" half (small numbers),
  // bump the overflow snapshot by one.
  if ((tifr_snapshot & _BV(TOV1)) && (icr < 0x8000)) {
    ovf_snapshot++;
  }
  return (ovf_snapshot << 16) | icr;
}

void setup() {
  Serial.begin(2000000);
  pinMode(8, INPUT);          // or INPUT_PULLUP if your source is open-collector

  // Timer1 normal mode
  TCCR1A = 0;

  // Enable noise canceller (ICNC1) + capture on RISING first (ICES1)
  // No prescaler (CS10) -> 1 tick = 0.0625 µs
  TCCR1B = _BV(ICNC1) | _BV(ICES1) | _BV(CS10);

  // Clear pending flags
  TIFR1 = _BV(ICF1) | _BV(TOV1);

  // Enable interrupts: Input Capture + Overflow
  TIMSK1 = _BV(ICIE1) | _BV(TOIE1);
}

ISR(TIMER1_OVF_vect) {
  ovfCount++;
}

ISR(TIMER1_CAPT_vect) {
  // Snapshot flags and counters *before* using them
  uint8_t  tifr = TIFR1;     // read flags (don’t clear)
  uint16_t icr  = ICR1;      // captured timer value
  uint32_t ovf  = ovfCount;  // software overflow count

  uint32_t stamp = make_extended_stamp(icr, tifr, ovf);

  if (waitingRising) {
    startStamp = stamp;
    TCCR1B &= ~_BV(ICES1);   // next: FALLING
    waitingRising = false;
  } else {
    endStamp = stamp;
    haveMeasurement = true;
    TCCR1B |= _BV(ICES1);    // next: RISING
    waitingRising = true;
  }
}

void loop() {
  if (haveMeasurement) {
    noInterrupts();
    uint32_t s = startStamp;
    uint32_t e = endStamp;
    haveMeasurement = false;
    interrupts();

    // 32-bit stamps naturally wrap every ~268 s; subtraction on uint32_t wraps correctly.
    uint32_t ticks32 = (uint32_t)(e - s);

    // Convert to microseconds: 1 tick = 0.0625 µs
    float us = (float)ticks32 * 0.0625f;

    Serial.println(us, 2);
  }
}




// // Measure HIGH time on D8 (ICP1) using Timer1 Input Capture
// // Sends 32-bit tick counts (no floats) over Serial at 1,000,000 baud.
// // Each tick = 1 / 16 MHz = 0.0625 µs.

// volatile uint32_t ovfCount = 0;
// volatile bool waitingRising = true;

// constexpr uint8_t RBITS = 6;           // 64-entry ring buffer
// constexpr uint8_t RSIZE = (1 << RBITS);
// volatile uint32_t rb[RSIZE];
// volatile uint8_t rhead = 0, rtail = 0;

// static inline bool rb_push(uint32_t v) {
//   uint8_t h = rhead;
//   uint8_t n = (uint8_t)(h + 1) & (RSIZE - 1);
//   if (n == rtail) return false; // buffer full: drop sample
//   rb[h] = v;
//   rhead = n;
//   return true;
// }
// static inline bool rb_pop(uint32_t &v) {
//   uint8_t t = rtail;
//   if (t == rhead) return false; // empty
//   v = rb[t];
//   rtail = (uint8_t)(t + 1) & (RSIZE - 1);
//   return true;
// }

// static inline uint32_t make_extended_stamp(uint16_t icr, uint8_t tifr_snapshot, uint32_t ovf_snapshot) {
//   if ((tifr_snapshot & _BV(TOV1)) && (icr < 0x8000)) {
//     ovf_snapshot++;
//   }
//   return (ovf_snapshot << 16) | icr;
// }

// ISR(TIMER1_OVF_vect) {
//   ovfCount++;
// }

// ISR(TIMER1_CAPT_vect) {
//   uint8_t  tifr = TIFR1;
//   uint16_t icr  = ICR1;
//   uint32_t ovf  = ovfCount;
//   uint32_t stamp = make_extended_stamp(icr, tifr, ovf);

//   static uint32_t startStampLocal = 0;

//   if (waitingRising) {
//     startStampLocal = stamp;
//     TCCR1B &= ~_BV(ICES1);   // next: FALLING
//     waitingRising = false;
//   } else {
//     uint32_t ticks = stamp - startStampLocal; // wraps naturally
//     rb_push(ticks);           // store in ring buffer (non-blocking)
//     TCCR1B |= _BV(ICES1);     // next: RISING
//     waitingRising = true;
//   }
// }

// void setup() {
//   Serial.begin(1000000);      // 1 Mbps
//   pinMode(8, INPUT);          // or INPUT_PULLUP if open collector

//   // Timer1: normal mode, no prescaler, noise canceler ON, capture rising first
//   TCCR1A = 0;
//   TCCR1B = _BV(ICNC1) | _BV(ICES1) | _BV(CS10);
//   TIFR1  = _BV(ICF1) | _BV(TOV1); // clear pending flags
//   TIMSK1 = _BV(ICIE1) | _BV(TOIE1); // enable interrupts
// }

// void loop() {
//   uint32_t ticks;
//   while (rb_pop(ticks)) {
//     // Send ticks as 4 bytes, little-endian (fast, compact)
//     Serial.write((uint8_t*)&ticks, 4);
//   }
// }


