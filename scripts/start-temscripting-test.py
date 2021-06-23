from temscript import GetInstrument

# for testing on the Titan microscope PC
print("Starting Test...")

instrument = GetInstrument()
gun = instrument.Gun
illumination = instrument.Illumination
projection = instrument.Projection
vacuum = instrument.Vacuum

illuminationMode = illumination.Mode
print("illuminationMode=%s" % illuminationMode)

condenserMode = illumination.CondenserMode
print("condenserMode=%s" % condenserMode)

htValue = gun.HTValue
print("HT1=%s" % htValue)

cameraLength = projection.CameraLength
print("cameraLength=%s" % cameraLength)

magnification = projection.Magnification
print("magnification=%s" % magnification)

projectionMode = projection.Mode
print("projectionMode=%s" % projectionMode)

projectionSubMode = projection.SubMode
print("projectionSubMode=%s" % projectionSubMode)

stemMagnification = illumination.StemMagnification
print("stemMagnification=%s" % stemMagnification)

beamBlanked = illumination.BeamBlanked
print("beamBlanked=%s" % beamBlanked)

illuminationMode = illumination.Mode
print("illuminationMode=%s" % illuminationMode)

illuminatedArea = illumination.IlluminatedArea
print("illuminatedArea=%s" % illuminatedArea)

dfMode = illumination.DFMode
print("dfMode=%s" % dfMode)

spotSizeIndex = illumination.SpotSizeIndex
print("spotSizeIndex=%s" % spotSizeIndex)

condenserMode = illumination.CondenserMode
print("condenserMode=%s" % condenserMode)

#convergenceAngle = illumination.ConvergenceAngle
#print("convergenceAngle=%s" % convergenceAngle)

print("Done.")