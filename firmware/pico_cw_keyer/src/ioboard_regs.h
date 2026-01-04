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

// -----------------------------------------------------------------------------
// Envelope shaping / key-click reduction
//
// Keep REG_TEXT_BUF offset stable. Place new registers AFTER the text buffer.
// Text buffer range: REG_TEXT_BUF .. REG_TEXT_BUF + TEXT_MAX_REGS - 1 (210..269)
// First free CW register: 270
// -----------------------------------------------------------------------------
#define REG_CW_ENV_BASE         (REG_TEXT_BUF + TEXT_MAX_REGS)   // 270

// Rise/Fall time in microseconds (0 => disable shaping / hard keying)
#define REG_CW_RISE_US          (REG_CW_ENV_BASE + 0)            // 270
#define REG_CW_FALL_US          (REG_CW_ENV_BASE + 1)            // 271

// Shape selector (0=linear; future: LUT-based raised cosine)
#define REG_CW_ENV_SHAPE        (REG_CW_ENV_BASE + 2)            // 272

// Max amplitude scaler (Q1.15: 0..32767 maps to 0.0..~1.0)
#define REG_CW_ENV_MAX_AMP_Q15  (REG_CW_ENV_BASE + 3)            // 273
