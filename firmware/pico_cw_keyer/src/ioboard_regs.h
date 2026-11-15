#pragma once
// -----------------------------------------------------------------------------
// I2C-Registermap des HL2-IO-Boards mit SOTA-CW-Keyer.
//
// Zugriff vom Pi: Protocol 1 -> HL2 C&C 0x3D (I2C2) -> Pico, I2C-Adresse 0x1D.
// Alle Register sind 8 bit breit und 0..255 adressiert. Ein HL2-Write
// überträgt genau ein Datenbyte. Ein HL2-Read liefert 4 Bytes ab der
// angefragten Registernummer (der Slave zählt pro Byte hoch).
//
// Gespiegelt in pi/backend/src/sota_cw/ioboard.py – bei Änderungen beide anpassen.
// -----------------------------------------------------------------------------
#include <stdint.h>

#define IOBOARD_I2C_ADDR        0x1D

// --- Standardregister (Nummern wie i2c_registers.h, jimahlstrom/HL2IOBoard) ---
#define REG_TX_FREQ_BYTE4       0    // höchstes Byte
#define REG_TX_FREQ_BYTE3       1
#define REG_TX_FREQ_BYTE2       2
#define REG_TX_FREQ_BYTE1       3
#define REG_TX_FREQ_BYTE0       4    // niedrigstes Byte, Write übernimmt Frequenz
#define REG_CONTROL             5    // Write 1 = Standardregister zurücksetzen
#define REG_INPUT_PINS          6    // Bit0 EXTTR (1 = RX), Bit1..5 In1..In5
#define REG_ANTENNA_TUNER       7    // nur gespeichert (kein ATU-Treiber in dieser Firmware)
#define REG_FAULT               8
#define REG_FIRMWARE_MAJOR      9
#define REG_FIRMWARE_MINOR      10
#define REG_RF_INPUTS           11   // 0 = normal, 1 = J9, 2 = J9 RX / J10 PureSignal TX
#define REG_FAN_SPEED           12   // 0..255

// --- SOTA-CW-Keyer (Bereich 200..255 ist für SDR-Software frei) ---
#define CW_REG_BASE             200

#define REG_CW_CMD              (CW_REG_BASE + 0)   // W: 0 idle, 1 start, 2 abort, 3 clear
#define REG_CW_STATUS           (CW_REG_BASE + 1)   // R: siehe CW_STATUS_*
#define REG_CW_WPM              (CW_REG_BASE + 2)   // 5..60
#define REG_PTT_LEAD_MS         (CW_REG_BASE + 3)   // 0..255 ms PTT vor erstem Zeichen
#define REG_PTT_TAIL_MS         (CW_REG_BASE + 4)   // 0..255 ms PTT nach letztem Zeichen
#define REG_FARNSWORTH_WPM      (CW_REG_BASE + 5)   // 0 = wie WPM
#define REG_WEIGHT_PCT          (CW_REG_BASE + 6)   // 50 = nominal, 25..75
#define REG_CW_ERROR            (CW_REG_BASE + 7)   // R: siehe CW_ERR_*
#define REG_CW_PROGRESS         (CW_REG_BASE + 8)   // R: gesendete Zeichen seit START (mod 256)
#define REG_CW_FIFO_LEVEL       (CW_REG_BASE + 9)   // R: Zeichen im FIFO
#define REG_CW_FIFO_DATA        (CW_REG_BASE + 10)  // W: ASCII-Zeichen anhängen
#define REG_CW_HEARTBEAT        (CW_REG_BASE + 11)  // W: beliebiger Wert, setzt Host-Watchdog zurück
#define REG_CW_WATCHDOG_S       (CW_REG_BASE + 12)  // 1..30 s ohne I2C-Write -> Taste los
#define REG_CW_KEY_DIRECT       (CW_REG_BASE + 13)  // W: 1 = Dauerträger (Tune), 0 = aus
#define REG_CW_API_VERSION      (CW_REG_BASE + 14)  // R
#define REG_CW_MAGIC            (CW_REG_BASE + 15)  // R: 0xC5

#define CW_CMD_IDLE        0
#define CW_CMD_START       1
#define CW_CMD_ABORT       2
#define CW_CMD_CLEAR       3

#define CW_STATUS_IDLE     0
#define CW_STATUS_RUNNING  1
#define CW_STATUS_DONE     2
#define CW_STATUS_ABORTED  3
#define CW_STATUS_ERROR    4
#define CW_STATUS_TUNE     5

#define CW_ERR_NONE            0
#define CW_ERR_FIFO_OVERFLOW   1
#define CW_ERR_HOST_WATCHDOG   2
#define CW_ERR_TUNE_TIMEOUT    3

#define CW_FIFO_SIZE        256   // Ringpuffer, nutzbar 255 Zeichen
#define CW_TUNE_MAX_US      (15u * 1000u * 1000u)
#define CW_KEYER_MAGIC      0xC5
#define CW_KEYER_API        1

#define FW_VERSION_MAJOR    2
#define FW_VERSION_MINOR    0
