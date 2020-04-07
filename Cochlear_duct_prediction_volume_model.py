path_to_volumes = 'PATH_TO_VOLUMES'
path_to_save_csv = 'PATH_TO_SAVE_CSV'
path_to_save_segmentations = 'PATH_TO_SAVE_SEGMENTATIONS'
path_to_save_models = 'PATH_TO_SAVE_MODELS'
nvidia_server_adress = 'NVIDIA_SERVER_ADRESS'
from pathlib import Path
for path in Path(path_to_volumes).rglob('*.nrrd'):
	[success, masterVolumeNode] = slicer.util.loadVolume(str(path), returnNode=True)
	# Create segmentation
	segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
	segmentationNode.CreateDefaultDisplayNodes() # only needed for display
	segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(masterVolumeNode)
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
	serverUrl = nvidia_server_adress
	effect.self().ui.serverComboBox.currentText = serverUrl
	effect.self().onClickFetchModels()
	effect.self().ui.segmentationModelSelector.currentText = "cochlear_duct"
	effect.self().onClickSegmentation()
	cochlea = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("cochlear_duct")
	segmentationNode.GetSegmentation().GetSegment(cochlea).SetColor(1,0,0)
	segmentEditorWidget.setCurrentSegmentID(cochlea)
	segmentEditorNode.SetMasterVolumeIntensityMaskRange(-810, 500)
	# Removing small islands
	# Islands effect
	segmentEditorWidget.setActiveEffectByName("Islands")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("Operation", 'KEEP_LARGEST_ISLAND')	
	effect.setParameter("MinimumSize", 100)
	effect.self().onApply()	
	#Turn mask range on
	segmentEditorNode.MasterVolumeIntensityMaskOn()
	#smoothing the cochlea
	# Smoothing effect
	segmentEditorWidget.setActiveEffectByName("Smoothing")
	effect = segmentEditorWidget.activeEffect()
	effect.setParameter("SmoothingMethod", "MEDIAN")
	effect.setParameter("KernelSizeMm", 0.3)	
	effect.self().onApply()
	#Turn mask range off
	segmentEditorNode.MasterVolumeIntensityMaskOff()
	## Create table	
	resultsTableNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLTableNode')
	## Use segmentStatistics to calculate the volume and export	
	import SegmentStatistics
	segStatLogic = SegmentStatistics.SegmentStatisticsLogic()
	segStatLogic.getParameterNode().SetParameter("Segmentation", segmentationNode.GetID())
	segStatLogic.getParameterNode().SetParameter("ScalarVolume", masterVolumeNode.GetID())
	segStatLogic.getParameterNode().SetParameter("LabelmapSegmentStatisticsPlugin.enabled","False")
	segStatLogic.getParameterNode().SetParameter("ScalarVolumeSegmentStatisticsPlugin.voxel_count.enabled","False")
	segStatLogic.computeStatistics()
	segStatLogic.exportToTable(resultsTableNode)
	segStatLogic.showTable(resultsTableNode)
	#prepare and save the segmentation	
	seg = getNode('Segmentation')
	##Get the segment vtk representation 
	segmentationNode = getNode("vtkMRMLSegmentationNode1")
	cochlea_vtk = segmentationNode.GetSegmentation().GetSegment(cochlea)
	##Create Model
	modelNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLModelNode')
	##Export segment to model
	slicer.modules.segmentations.logic().ExportSegmentToRepresentationNode(cochlea_vtk, modelNode)
	##  save model
	saveNode(modelNode, path_to_save_models +(path.name[0:-5])+ '.obj')
	saveNode(seg, path_to_save_segmentations + (path.name[0:-5])+'.seg.nrrd')
	##save the table as cvs file
	saveNode(resultsTableNode, path_to_save_csv'+(path.name[0:-5])+'.csv')
	slicer.mrmlScene.Clear(0)

