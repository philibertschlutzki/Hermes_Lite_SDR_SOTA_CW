cmake_minimum_required(VERSION 3.13)

include($ENV{PICO_SDK_PATH}/external/pico_sdk_import.cmake)

project(pico_cw_keyer C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)

pico_sdk_init()

add_executable(pico_cw_keyer
  src/main.c
  src/keyer.c
  src/cw_morse.c
)

target_include_directories(pico_cw_keyer PRIVATE src)

# Keying-Ausgänge anpassen: cmake -DKEY_GPIO=22 -DPTT_GPIO=8 ..
if(DEFINED KEY_GPIO)
  target_compile_definitions(pico_cw_keyer PRIVATE KEY_GPIO=${KEY_GPIO})
endif()
if(DEFINED PTT_GPIO)
  target_compile_definitions(pico_cw_keyer PRIVATE PTT_GPIO=${PTT_GPIO})
endif()

target_link_libraries(pico_cw_keyer
  pico_stdlib
  pico_i2c_slave
  hardware_gpio
  hardware_i2c
  hardware_pwm
  hardware_watchdog
)

pico_enable_stdio_usb(pico_cw_keyer 0)
pico_enable_stdio_uart(pico_cw_keyer 0)

pico_add_extra_outputs(pico_cw_keyer)
