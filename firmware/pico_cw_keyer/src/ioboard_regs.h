#pragma once
#include <stdint.h>

// CW Job register base
#define CW_REG_BASE        200

#define REG_CW_CMD         (CW_REG_BASE + 0)
#define REG_CW_STATUS      (CW_REG_BASE + 1)
#define REG_CW_WPM         (CW_REG_BASE + 2)
#define REG_PTT_LEAD_MS    (CW_REG_BASE + 3)
#define REG_PTT_TAIL_MS    (CW_REG_BASE + 4)
#define REG_TEXT_LEN       (CW_REG_BASE + 5)
#define REG_PROGRESS       (CW_REG_BASE + 6)
#define REG_ERROR_CODE     (CW_REG_BASE + 7)
#define REG_TEXT_BUF       (CW_REG_BASE + 8)

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
