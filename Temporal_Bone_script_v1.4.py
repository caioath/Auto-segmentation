import time
from pathlib import Path
for path in Path('PATH_TO_FILES_FOLDER').rglob('*.nii.gz'):
	[success, masterVolumeNode] = slicer.util.loadVolume(str(path), returnNode=True)
	# Resample the volume to 0.25mm spacing
	parameters = {"outputPixelSpacing":"0.25,0.25,0.25", "InputVolume":masterVolumeNode,"interpolationType":'linear',"OutputVolume":masterVolumeNode}
	slicer.cli.run(slicer.modules.resamplescalarvolume, None, parameters)
	time.sleep(1)
	# Create segmentation with Bony labyrinth segment
	segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
	segmentationNode.CreateDefaultDisplayNodes() # only needed for display
	segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
	addedSegmentID = segmentationNode.GetSegmentation().AddEmptySegment("bony_lab")
	# Create segment editor to get access to effects
	segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
	segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
	segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
	segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
	segmentEditorWidget.setSegmentationNode(segmentationNode)
	segmentEditorWidget.setMasterVolumeNode(masterVolumeNode)
	# NVIDIA auto segmentation
	segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
	effect = segmentEditorWidget.activeEffect()
	serverUrl = "http://LINK/v1/models"
	effect.self().ui.serverComboBox.currentText = serverUrl
	effect.self().onClickFetchModels()
	effect.self().ui.segmentationModelSelector.currentText = "inner_ear"
	effect.self().onClickSegmentation()
	inner_ear = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("inner_ear")
	segmentationNode.GetSegmentation().GetSegment(inner_ear).SetColor(1,0,0)
	segmentEditorWidget.setCurrentSegmentID(inner_ear)
	segmentEditorNode.SetMasterVolumeIntensityMaskRange(-410, 750)
	#Turn mask range on
	segmentEditorNode.MasterVolumeIntensityMaskOn()
	#growing the membranous labyrinth
	# Margin effect
	segmentEditorWidget.setActiveEffectByName("Margin")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("MarginSizeMm", 0.3)
	effect.self().onApply()
	# Removing small islands
	# Islands effect
	segmentEditorWidget.setActiveEffectByName("Islands")
	effect = segmentEditorWidget.activeEffect()
	#effect.setParameter("Operation", REMOVE_SMALL_ISLANDS)
	#effect.setParameter("MinimumSize", 200)
	#effect.self().onApply()
	# Turn mask off
	segmentEditorNode.MasterVolumeIntensityMaskOff()
	slicer.vtkMRMLSegmentEditorNode.OverwriteNone
	segmentEditorWidget.setCurrentSegmentID('bony_lab')
	#Copying the inner ear segment to bony labyrinth
	# Logical effect
	segmentEditorWidget.setActiveEffectByName("Logical operators")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("Operation", 'COPY')
	effect.setParameter("ModifierSegmentID", inner_ear)
	effect.setParameter("BypassMasking", 1)
	effect.self().onApply()
	# Define the Mask range for bony labyrinth
	segmentEditorNode.SetMasterVolumeIntensityMaskRange(650, 3000)
	#Turn mask range on
	segmentEditorNode.MasterVolumeIntensityMaskOn()
	#segmenting the bony labyrinth from the inner ear 
	# Margin effect
	segmentEditorWidget.setActiveEffectByName("Margin")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("MarginSizeMm", 2.3)
	effect.self().onApply()
	segmentEditorNode.MasterVolumeIntensityMaskOff()
	## Segmenting the other structures
	segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
	effect = segmentEditorWidget.activeEffect()
	# Autosegmentation of Ossicles
	effect.self().ui.segmentationModelSelector.currentText = "ossicles_v4"
	effect.self().onClickSegmentation()
	ossicles = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("ossicles_v4")
	segmentationNode.GetSegmentation().GetSegment(ossicles).SetColor(0.9,1,0.7)
	segmentEditorWidget.setCurrentSegmentID(ossicles)
	segmentEditorNode.SetMasterVolumeIntensityMaskRange(0, 2500)
	segmentEditorNode.MasterVolumeIntensityMaskOn()
	segmentEditorWidget.setActiveEffectByName("Smoothing")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("SmoothingMethod", "MEDIAN")
	effect.setParameter("KernelSizeMm", 0.3)
	effect.self().onApply()
	segmentEditorNode.MasterVolumeIntensityMaskOff()
	# Autosegmentation of Facial Nerve
	segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
	effect = segmentEditorWidget.activeEffect()
	effect.self().ui.segmentationModelSelector.currentText = "facial_nerve_v3"
	effect.self().onClickSegmentation()
	facial_nerve = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("facial_nerve")
	segmentationNode.GetSegmentation().GetSegment(facial_nerve).SetColor(1,1,0)
	segmentEditorWidget.setCurrentSegmentID(facial_nerve)
	# Define the Mask range for facial nerve
	segmentEditorNode.SetMasterVolumeIntensityMaskRange(-300, 500)
	#Turn mask range on
	segmentEditorNode.MasterVolumeIntensityMaskOn()
	#smoothing facial nerve by margin 
	# Margin effect
	segmentEditorWidget.setActiveEffectByName("Margin")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("MarginSizeMm", 0.3)
	effect.self().onApply()
	segmentEditorNode.MasterVolumeIntensityMaskOff()
	# Autosegmentation of Sigmoid sinus
	segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
	effect = segmentEditorWidget.activeEffect()
	effect.self().ui.segmentationModelSelector.currentText = "sigmoid_sinus_v4"
	effect.self().onClickSegmentation()
	sigmoid_sinus = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("sigmoid_v4")
	segmentEditorWidget.setCurrentSegmentID(sigmoid_sinus)
	segmentEditorNode.SetMasterVolumeIntensityMaskRange(-300, 500)
	segmentEditorNode.MasterVolumeIntensityMaskOn()
	segmentEditorWidget.setActiveEffectByName("Margin")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("MarginSizeMm", 0.3)
	effect.self().onApply()
	segmentEditorNode.MasterVolumeIntensityMaskOff()
	seg = getNode('Segmentation')
	saveNode(seg, 'PATH_TO_SEGMENTATIONS_FOLDER/'+str(path.name[0:-7])+'.seg.nrrd')
	slicer.mrmlScene.Clear(0)
