#include "temscript.h"
#include "defines.h"
#include "types.h"

DOUBLE_PROPERTY_GETTER(Gun1, HighVoltageOffset)
DOUBLE_PROPERTY_SETTER(Gun1, HighVoltageOffset)

static PyObject* Gun1_GetHighVoltageOffsetRange(Gun1 *self)
{
    double min, max;
    HRESULT result = self->iface->raw_GetHighVoltageOffsetRange(&min, &max);
    if (FAILED(result)) {
        raiseComError(result);
        return NULL;
    }

    return Py_BuildValue("dd", min, max);
}

static PyGetSetDef Gun1_getset[] = {
    {"HighVoltageOffset",         (getter)&Gun1_get_HighVoltageOffset, (setter)&Gun1_set_HighVoltageOffset, NULL, NULL},
    {NULL}  /* Sentinel */
};

static PyMethodDef Gun1_methods[] = {
    {"GetHighVoltageOffsetRange",      (PyCFunction)Gun1_GetHighVoltageOffsetRange, METH_NOARGS, NULL},
    {NULL}  /* Sentinel */
};


IMPLEMENT_WRAPPER(Gun1, TEMScripting::Gun1, Gun1_getset, Gun1_methods)
