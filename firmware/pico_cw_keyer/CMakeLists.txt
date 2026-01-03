cmake_minimum_required(VERSION 3.13)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico_cw_keyer C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(pico_cw_keyer
  src/main.c
  src/cw_morse.c
  src/outputs.c
)

target_include_directories(pico_cw_keyer PRIVATE src)

target_link_libraries(pico_cw_keyer pico_stdlib hardware_gpio)

pico_enable_stdio_usb(pico_cw_keyer 1)
pico_enable_stdio_uart(pico_cw_keyer 0)

pico_add_extra_outputs(pico_cw_keyer)
