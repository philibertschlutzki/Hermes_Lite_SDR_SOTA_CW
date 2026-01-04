#pragma once
#include <stdint.h>

// CW Job register base
#define CW_REG_BASE        200

// --- Control/Status ---
#define REG_CW_CMD         (CW_REG_BASE + 0)
#define REG_CW_STATUS      (CW_REG_BASE + 1)

// --- TX timing params ---
#define REG_CW_WPM              (CW_REG_BASE + 2)
#define REG_PTT_LEAD_MS         (CW_REG_BASE + 3)
#define REG_PTT_TAIL_MS         (CW_REG_BASE + 4)
#define REG_TEXT_LEN            (CW_REG_BASE + 5)
#define REG_PROGRESS            (CW_REG_BASE + 6)
#define REG_ERROR_CODE          (CW_REG_BASE + 7)

// New parameters to improve CW TX quality (timing/spacing)
// - Farnsworth WPM: slows down spacing (character/word gaps) while keeping element speed at REG_CW_WPM.
//   If 0, firmware treats it as REG_CW_WPM.
// - Weight percent: scales key-down time of dits/dahs. 50 = nominal.
//   Valid range enforced in firmware.
#define REG_FARNSWORTH_WPM      (CW_REG_BASE + 8)
#define REG_WEIGHT_PCT          (CW_REG_BASE + 9)

// Text buffer: 2 ASCII bytes per 16-bit register
#define REG_TEXT_BUF            (CW_REG_BASE + 10)

#define CW_STATUS_IDLE     0
#define CW_STATUS_RUNNING  1
#define CW_STATUS_DONE     2
#define CW_STATUS_ABORTED  3
#define CW_STATUS_ERROR    4

#define CW_CMD_IDLE        0
#define CW_CMD_START       1
#define CW_CMD_ABORT       2

// Limits
#define TEXT_MAX_CHARS     120
#define TEXT_MAX_REGS      ((TEXT_MAX_CHARS + 1) / 2)
