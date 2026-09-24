#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "capture_protocol.h"

int main() {
  using namespace capture_protocol;
  Request request{};
  assert(parseRequest("CAPTURE 0123456789abcdef0123456789abcdef swipe_left 200", request));
  assert(request.samples == 200 && strcmp(request.label, "swipe_left") == 0);
  assert(!parseRequest("CAPTURE invalid swipe_left 200", request));
  assert(!parseRequest("CAPTURE 0123456789abcdef0123456789abcdef ../escape 200", request));
  assert(!parseRequest("CAPTURE 0123456789abcdef0123456789abcdef swipe_left 0", request));
  assert(!parseRequest("CAPTURE 0123456789abcdef0123456789abcdef swipe_left 501", request));
  assert(!parseRequest("CAPTURE 0123456789abcdef0123456789abcdef swipe_left -1", request));
  assert(!parseRequest("CAPTURE 0123456789abcdef0123456789abcdef swipe_left 200 extra", request));
  assert(!parseRequest("CAPTURE 0123456789abcdef0123456789abcdef swipe_left 999999999999999999999999", request));
  assert(crc32("123456789", 9) == 0xCBF43926u);
  assert(crc32("456789", 6, crc32("123", 3)) == 0xCBF43926u);
  puts("Native command parser and CRC tests passed (artificial protocol fixtures).");
}
