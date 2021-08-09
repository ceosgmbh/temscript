#include "temscript.h"
#include "defines.h"
#include "types.h"

ENUM_PROPERTY_GETTER(Gun1, HTState, TEMScripting::HightensionState)
ENUM_PROPERTY_SETTER(Gun1, HTState, TEMScripting::HightensionState)
DOUBLE_PROPERTY_GETTER(Gun1, HTValue)
DOUBLE_PROPERTY_SETTER(Gun1, HTValue)
DOUBLE_PROPERTY_GETTER(Gun1, HTMaxValue)
VECTOR_PROPERTY_GETTER(Gun1, Shift)
VECTOR_PROPERTY_SETTER(Gun1, Shift)
VECTOR_PROPERTY_GETTER(Gun1, Tilt)
VECTOR_PROPERTY_SETTER(Gun1, Tilt)
DOUBLE_PROPERTY_GETTER(Gun1, HighVoltageOffset)
DOUBLE_PROPERTY_SETTER(Gun1, HighVoltageOffset)

static PyGetSetDef Gun1_getset[] = {
//    {"HTState",         (getter)&Gun1_get_HTState, (setter)&Gun1_set_HTState, NULL, NULL},
//    {"HTValue",         (getter)&Gun1_get_HTValue, (setter)&Gun1_set_HTValue, NULL, NULL},
//    {"HTMaxValue",      (getter)&Gun1_get_HTMaxValue, NULL, NULL, NULL},
//    {"Shift",           (getter)&Gun1_get_Shift, (setter)&Gun1_set_Shift, NULL, NULL},
//    {"Tilt",            (getter)&Gun1_get_Tilt, (setter)&Gun1_set_Tilt, NULL, NULL},
    {"HighVoltageOffset",  (getter)&Gun1_get_HighVoltageOffset, (setter)&Gun1_set_HighVoltageOffset, NULL, NULL},
    {NULL}  /* Sentinel */
};

IMPLEMENT_WRAPPER(Gun1, TEMScripting::Gun1, Gun1_getset, 0)
// IMPLEMENT_WRAPPER(Gun1, TEMScripting::Gun, Gun1_getset, 0)
// IMPLEMENT_WRAPPER2(Gun1, TEMScripting::Gun, Gun1_getset, 0)
