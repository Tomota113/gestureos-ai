#pragma once
#include <stddef.h>
#include <stdint.h>

namespace capture_protocol {
struct Request {
  char id[33];
  char label[33];
  uint16_t samples;
};

bool parseRequest(const char* line, Request& request);
uint32_t crc32(const char* data, size_t size, uint32_t previous = 0);
}  // namespace capture_protocol
