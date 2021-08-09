#include "temscript.h"
#include "defines.h"
#include "types.h"

DOUBLE_PROPERTY_GETTER(Gun1, HighVoltageOffset)
DOUBLE_PROPERTY_SETTER(Gun1, HighVoltageOffset)

static PyGetSetDef Gun1_getset[] = {
    {"HighVoltageOffset",  (getter)&Gun1_get_HighVoltageOffset, (setter)&Gun1_set_HighVoltageOffset, NULL, NULL},
    //{"GetHighVoltageOffsetRange",      (getter)&Gun1_get_HighVoltageOffsetRange, NULL, NULL, NULL},
    {NULL}  /* Sentinel */
};

IMPLEMENT_WRAPPER(Gun1, TEMScripting::Gun1, Gun1_getset, 0)
// IMPLEMENT_WRAPPER(Gun1, TEMScripting::Gun, Gun1_getset, 0)
// IMPLEMENT_WRAPPER2(Gun1, TEMScripting::Gun, Gun1_getset, 0)
