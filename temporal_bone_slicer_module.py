import os
import unittest
import logging
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin

#
# TemporalBoneAutosegmentation
#

class TemporalBoneAutosegmentation(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Temporal Bone AI Auto-segmentation"  # TODO: make this more human readable by adding spaces
    self.parent.categories = ["Segmentation"]  # TODO: set categories (folders where the module shows up in the module selector)
    self.parent.dependencies = []  # TODO: add here list of module names that this module requires
    self.parent.contributors = ["Caio Neves (UnB)"]  # TODO: replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This module allows the auto-segmentation of structures of the temporal bone from CT scan volumes through AI.
"""  # TODO: update with short description of the module
    self.parent.helpText += self.getDefaultModuleDocumentationLink()  # TODO: verify that the default URL is correct or change it to the actual documentation
    self.parent.acknowledgementText = """
This module was developed by Caio Neves, MD (University of Brasilia - BRA).
"""  # TODO: replace with organization, grant and thanks.

#
# TemporalBoneAutosegmentationWidget
#

class TemporalBoneAutosegmentationWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent=None):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.__init__(self, parent)
    VTKObservationMixin.__init__(self)  # needed for parameter node observation
    self.logic = None
    self._parameterNode = None

  def setup(self):
    """
    Called when the user opens the module the first time and the widget is initialized.
    """
    ScriptedLoadableModuleWidget.setup(self)

    # Load widget from .ui file (created by Qt Designer)
    uiWidget = slicer.util.loadUI(self.resourcePath('UI/TemporalBoneAutosegmentation.ui'))
    self.layout.addWidget(uiWidget)
    self.ui = slicer.util.childWidgetVariables(uiWidget)

    # Set scene in MRML widgets. Make sure that in Qt designer
    # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
    # "setMRMLScene(vtkMRMLScene*)" slot.
    uiWidget.setMRMLScene(slicer.mrmlScene)

    # Create a new parameterNode
    # This parameterNode stores all user choices in parameter values, node selections, etc.
    # so that when the scene is saved and reloaded, these settings are restored.
    self.logic = TemporalBoneAutosegmentationLogic()
    self.ui.parameterNodeSelector.addAttribute("vtkMRMLScriptedModuleNode", "ModuleName", self.moduleName)
    self.setParameterNode(self.logic.getParameterNode())

    # Connections
    self.ui.parameterNodeSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.setParameterNode)
    self.ui.applyButton.connect('clicked(bool)', self.onApplyButton)

    # These connections ensure that whenever user changes some settings on the GUI, that is saved in the MRML scene
    # (in the selected parameter node).
    self.ui.inputSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.updateParameterNodeFromGUI)
    self.ui.DirectoryButton.connect("directory(QString)", self.updateParameterNodeFromGUI)
    self.ui.exportlabelmapsCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.exportOBJCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    self.ui.medianFilterCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)
    #self.ui.exportDICOMCheckBox.connect("toggled(bool)", self.updateParameterNodeFromGUI)

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def cleanup(self):
    """
    Called when the application closes and the module widget is destroyed.
    """
    self.removeObservers()

  def setParameterNode(self, inputParameterNode):
    """
    Adds observers to the selected parameter node. Observation is needed because when the
    parameter node is changed then the GUI must be updated immediately.
    """

    if inputParameterNode:
      self.logic.setDefaultParameters(inputParameterNode)

    # Set parameter node in the parameter node selector widget
    wasBlocked = self.ui.parameterNodeSelector.blockSignals(True)
    self.ui.parameterNodeSelector.setCurrentNode(inputParameterNode)
    self.ui.parameterNodeSelector.blockSignals(wasBlocked)
    
    if inputParameterNode == self._parameterNode:
      # No change
      return

    # Unobserve previusly selected parameter node and add an observer to the newly selected.
    # Changes of parameter node are observed so that whenever parameters are changed by a script or any other module
    # those are reflected immediately in the GUI.
    if self._parameterNode is not None:
      self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    if inputParameterNode is not None:
      self.addObserver(inputParameterNode, vtk.vtkCommand.ModifiedEvent, self.updateGUIFromParameterNode)
    self._parameterNode = inputParameterNode

    # Initial GUI update
    self.updateGUIFromParameterNode()

  def updateGUIFromParameterNode(self, caller=None, event=None):
    """
    This method is called whenever parameter node is changed.
    The module GUI is updated to show the current state of the parameter node.
    """

    # Disable all sections if no parameter node is selected
    #self.ui.basicCollapsibleButton.enabled = self._parameterNode is not None
    #self.ui.advancedCollapsibleButton.enabled = self._parameterNode is not None
    if self._parameterNode is None:
      return

    # Update each widget from parameter node
    # Need to temporarily block signals to prevent infinite recursion (MRML node update triggers
    # GUI update, which triggers MRML node update, which triggers GUI update, ...)

    wasBlocked = self.ui.inputSelector.blockSignals(True)
    self.ui.inputSelector.setCurrentNode(self._parameterNode.GetNodeReference("InputVolume"))
    self.ui.inputSelector.blockSignals(wasBlocked)

    wasBlocked = self.ui.exportlabelmapsCheckBox.blockSignals(True)
    self.ui.exportlabelmapsCheckBox.checked = (self._parameterNode.GetParameter("exportlabelmaps") == "true")
    self.ui.exportlabelmapsCheckBox.blockSignals(wasBlocked)

    wasBlocked = self.ui.exportOBJCheckBox.blockSignals(True)
    self.ui.exportOBJCheckBox.checked = (self._parameterNode.GetParameter("exportOBJ") == "true")
    self.ui.exportOBJCheckBox.blockSignals(wasBlocked)

    wasBlocked = self.ui.medianFilterCheckBox.blockSignals(True)
    self.ui.medianFilterCheckBox.checked = (self._parameterNode.GetParameter("medianFilter") == "true")
    self.ui.medianFilterCheckBox.blockSignals(wasBlocked)

    wasBlocked = self.ui.exportDICOMcheckBox.blockSignals(True)
    self.ui.exportDICOMcheckBox.checked = (self._parameterNode.GetParameter("exportDICOM") == "true")
    self.ui.exportDICOMcheckBox.blockSignals(wasBlocked)


    # Update buttons states and tooltips
    if self._parameterNode.GetNodeReference("InputVolume"):
      self.ui.applyButton.toolTip = "Run the algorithm."
      self.ui.applyButton.enabled = True
    else:
      self.ui.applyButton.toolTip = "Select input volume nodes"
      self.ui.applyButton.enabled = False

  def updateParameterNodeFromGUI(self, caller=None, event=None):
    """
    This method is called when the user makes any change in the GUI.
    The changes are saved into the parameter node (so that they are restored when the scene is saved and loaded).
    """

    if self._parameterNode is None:
      return

    self._parameterNode.SetNodeReferenceID("InputVolume", self.ui.inputSelector.currentNodeID)
    self._parameterNode.SetParameter("directory", self.ui.DirectoryButton.directory)
    self._parameterNode.SetParameter("exportlabelmaps", "true" if self.ui.exportlabelmapsCheckBox.checked else "false")
    self._parameterNode.SetParameter("exportOBJ", "true" if self.ui.exportOBJCheckBox.checked else "false")
    self._parameterNode.SetParameter("medianFilter", "true" if self.ui.medianFilterCheckBox.checked else "false")
    self._parameterNode.SetParameter("exportDICOM", "true" if self.ui.exportDICOMcheckBox.checked else "false")


  def onApplyButton(self):
    """
    Run processing when user clicks "Apply" button.
    """
    try:
      self.logic.run(self.ui.inputSelector.currentNode(), self.ui.DirectoryButton.directory, self.ui.exportlabelmapsCheckBox.checked,
        self.ui.exportOBJCheckBox.checked, self.ui.medianFilterCheckBox.checked, self.ui.exportDICOMcheckBox.checked)
    except Exception as e:
      slicer.util.errorDisplay("Failed to compute results: "+str(e))
      import traceback
      traceback.print_exc()


#
# TemporalBoneAutosegmentationLogic
#

class TemporalBoneAutosegmentationLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setDefaultParameters(self, parameterNode):
    """
    Initialize parameter node with default settings.
    """
    if not parameterNode.GetParameter("exportOBJ"):
      parameterNode.SetParameter("exportOBJ", "True")
    if not parameterNode.GetParameter("exportlabelmaps"):
      parameterNode.SetParameter("exportlabelmaps", "True")
    if not parameterNode.GetParameter("exportDICOM"):
      parameterNode.SetParameter("exportDICOM", "True")

  def run(self, inputVolume, directory, exportlabelmaps=True, exportOBJ=True, medianFilter=True, exportDICOM=True, showResult=True):
    """
    Run the processing algorithm.
    Can be used without GUI widget.
    :param inputVolume: volume to be segmented
    :param exportOBJ: export to OBJ files
    :param exportlabelmaps: export to labelmaps
    :param medianFilter: Whether the medial filter is used for improving the segmentation
    :param exportDICOM: Whether the isotropic volume is exported as a DICOM series
    :param showResult: show output volume in slice viewers
    """

    if not inputVolume:
      raise ValueError("Input volume is invalid")

    logging.info('Processing started')

    # Perform the temporal bone autosegmentation
    InputVolume: inputVolume.GetID()
    spacing = inputVolume.GetSpacing()[2]
    # resample
    if spacing<= 0.25:
        parameters = {"outputPixelSpacing":"0.25,0.25,0.25", "InputVolume":inputVolume,"interpolationType":'linear',"OutputVolume":inputVolume}
        slicer.cli.runSync(slicer.modules.resamplescalarvolume, None, parameters)
    else:
        parameters = {"outputPixelSpacing":"0.25,0.25,0.25", "InputVolume":inputVolume,"interpolationType":'bspline',"OutputVolume":inputVolume}
        slicer.cli.runSync(slicer.modules.resamplescalarvolume, None, parameters)
    print('\nResampling...\n')
    spacing = inputVolume.GetSpacing()[2]
    volumeName = inputVolume.GetName()
    # Create segmentation
    segmentationNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)
    otic_capsule_segment = segmentationNode.GetSegmentation().AddEmptySegment("otic_capsule")
    # Create segment editor to get access to effects
    segmentEditorWidget = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget.setMRMLSegmentEditorNode(segmentEditorNode)
    segmentEditorWidget.setSegmentationNode(segmentationNode)
    segmentEditorWidget.setMasterVolumeNode(inputVolume)

    segmentationNode1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode")
    segmentationNode1.CreateDefaultDisplayNodes() # only needed for display
    segmentationNode1.SetReferenceImageGeometryParameterFromVolumeNode(inputVolume)
    # Create segment editor to get access to effects
    segmentEditorWidget1 = slicer.qMRMLSegmentEditorWidget()
    segmentEditorWidget1.setMRMLScene(slicer.mrmlScene)
    segmentEditorNode1 = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentEditorNode")
    segmentEditorWidget1.setMRMLSegmentEditorNode(segmentEditorNode1)
    segmentEditorWidget1.setSegmentationNode(segmentationNode1)
    segmentEditorWidget1.setMasterVolumeNode(inputVolume)

    ## Autosegmentation of the otic capsule
    # NVIDIA auto segmentation
    segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
    effect = segmentEditorWidget.activeEffect()
    serverUrl = "http://tbone.onthewifi.com:956/v1/models"
    effect.self().ui.serverComboBox.currentText = serverUrl
    effect.self().onClickFetchModels()
    effect.self().ui.segmentationModelSelector.currentText = "inner_ear"
    effect.self().onClickSegmentation()
    inner_ear = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("inner_ear")
    segmentEditorWidget.setCurrentSegmentID(inner_ear)
    segmentationNode.GetSegmentation().GetSegment(inner_ear).SetColor(1,0,0)
    segmentationNode.GetSegmentation().GetSegment(otic_capsule_segment).SetColor(0.89,0.92,0.65)
    segmentEditorNode.SetMasterVolumeIntensityMaskRange(-300, 550)
    #Turn mask range on
    segmentEditorNode.MasterVolumeIntensityMaskOn()
    #growing the membranous labyrinth
    # Margin effect
    segmentEditorWidget.setActiveEffectByName("Margin")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MarginSizeMm", 0.3)
    effect.self().onApply()
    segmentEditorWidget.setCurrentSegmentID('otic_capsule')
    #Copying the inner ear segment to otic capsule
    # Logical effect
    segmentEditorWidget.setActiveEffectByName("Logical operators")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("Operation", 'COPY')
    effect.setParameter("ModifierSegmentID", inner_ear)
    effect.setParameter("BypassMasking", 1)
    effect.self().onApply()
    # Define the Mask range for bony labyrinth
    segmentEditorNode.SetMasterVolumeIntensityMaskRange(650, 2500)
    #Turn mask range on
    segmentEditorNode.MasterVolumeIntensityMaskOn()
    #segmenting the otic capsule from the inner ear 
    # Margin effect
    segmentEditorWidget.setActiveEffectByName("Margin")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MarginSizeMm", spacing*5)
    effect.self().onApply()
    segmentEditorNode.MasterVolumeIntensityMaskOff()
    # Islands effect
    segmentEditorWidget.setActiveEffectByName("Islands")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("Operation", 'KEEP_LARGEST_ISLAND')	
    effect.self().onApply()
    #Make the inner ear not visible to export only the otic capsule
    #segmentationNode.GetDisplayNode().SetSegmentVisibility(inner_ear, False)
	#copy the inner ear segment to another segmentation Node
    #segmentationNode1.GetSegmentation().CopySegmentFromSegmentation(segmentationNode.GetSegmentation(),inner_ear)
    # Remove the inner ear to export only the otic capsule
    segmentationNode.GetSegmentation().RemoveSegment(inner_ear)
    
    if exportlabelmaps==True:
      #Create labelmap for otic capsule and export the segment
      oticcapsule_labelmap = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      oticcapsule_labelmap.SetName('oticcapsule_labelmap')
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, oticcapsule_labelmap, inputVolume)
      slicer.util.saveNode(oticcapsule_labelmap, directory+'/oticcapsule_labelmap.nrrd')

    if exportOBJ==True:
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      segnumber = shNode.GetItemByDataNode(segmentationNode)
      shNode.SetItemName(segnumber, volumeName+'_otic capsule')
      segmentIDs = vtk.vtkStringArray()
      segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
      slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(directory,
        segmentationNode, segmentIDs, "OBJ", True,  1.0, False)

	#copy the otic capsule segment to another segmentation Node
    segmentationNode1.GetSegmentation().CopySegmentFromSegmentation(segmentationNode.GetSegmentation(),otic_capsule_segment)
	
    # Remove the otic capsule after exporting
    segmentationNode.GetSegmentation().RemoveSegment('otic_capsule')

    # Autosegmentation of the ossicles
    segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
    effect = segmentEditorWidget.activeEffect()
    effect.self().ui.segmentationModelSelector.currentText = 'ossicles'
    effect.self().onClickSegmentation()
    ossicles = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("ossicles")
    segmentationNode.GetSegmentation().GetSegment(ossicles).SetColor(1,1,0.88)
    segmentEditorWidget.setCurrentSegmentID(ossicles)
    # Islands effect
    segmentEditorWidget.setActiveEffectByName("Islands")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("Operation", 'REMOVE_SMALL_ISLANDS')
    effect.setParameter("MinimumSize", 50)
    effect.self().onApply()
    
    if exportlabelmaps==True:
      #Create labelmap for ossicles and export the segment
      ossicles_labelmap = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      ossicles_labelmap.SetName('ossicles_labelmap')
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, ossicles_labelmap, inputVolume)
      slicer.util.saveNode(ossicles_labelmap, directory+'/ossicles_labelmap.nrrd')

    if exportOBJ==True:
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      segnumber = shNode.GetItemByDataNode(segmentationNode)
      shNode.SetItemName(segnumber, volumeName+'_ossicles')
      segmentIDs = vtk.vtkStringArray()
      segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
      slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(directory,
        segmentationNode, segmentIDs, "OBJ", True,  1.0, False)

	#copy the ossicles segment to another segmentation Node
    segmentationNode1.GetSegmentation().CopySegmentFromSegmentation(segmentationNode.GetSegmentation(),ossicles)
	
    # Remove the ossicles after exporting
    segmentationNode.GetSegmentation().RemoveSegment(ossicles)

    # Autosegmentation of Cochlear duct
    segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
    effect = segmentEditorWidget.activeEffect()
    effect.self().ui.segmentationModelSelector.currentText = "cochlear_duct"
    effect.self().onClickSegmentation()
    cochlear_duct = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("cochlear_duct")
    segmentEditorWidget.setCurrentSegmentID(cochlear_duct)
    segmentationNode.GetSegmentation().GetSegment(cochlear_duct).SetColor(1,0,0)
    segmentEditorNode.SetMasterVolumeIntensityMaskRange(-410, 750)
    #Turn mask range on
    segmentEditorNode.MasterVolumeIntensityMaskOn()
    #growing the membranous labyrinth
    # Margin effect
    segmentEditorWidget.setActiveEffectByName("Margin")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("MarginSizeMm", 0.3)
    effect.self().onApply()
    
    if exportlabelmaps==True:
      #Create labelmap for cochlear duct and export the segment
      cochlear_duct_labelmap = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      cochlear_duct_labelmap.SetName('cochlear_duct_labelmap')
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, cochlear_duct_labelmap, inputVolume)
      slicer.util.saveNode(cochlear_duct_labelmap, directory+'/cochlear_duct_labelmap.nrrd')

    if exportOBJ==True:
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      segnumber = shNode.GetItemByDataNode(segmentationNode)
      shNode.SetItemName(segnumber, volumeName+'_cochlear_duct')
      segmentIDs = vtk.vtkStringArray()
      segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
      slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(directory,
        segmentationNode, segmentIDs, "OBJ", True,  1.0, False)  
	
	#copy the cochlear_duct segment to another segmentation Node
    segmentationNode1.GetSegmentation().CopySegmentFromSegmentation(segmentationNode.GetSegmentation(),cochlear_duct)
	
    # Remove the cochlear_duct after exporting
    segmentationNode.GetSegmentation().RemoveSegment(cochlear_duct)

    if medianFilter==True:
      volumesLogic = slicer.modules.volumes.logic()
      median = volumesLogic.CloneVolume(slicer.mrmlScene, inputVolume, 'Volume_median_filter')
    
      parameters = {"neighborhood":"1,1,1", "inputVolume":inputVolume,"outputVolume":median}
      slicer.cli.runSync(slicer.modules.medianimagefilter, None, parameters)
    
      segmentationNode.SetReferenceImageGeometryParameterFromVolumeNode(median)
      segmentEditorWidget.setMasterVolumeNode(median)

    # Autosegmentation of Facial Nerve
    segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
    effect = segmentEditorWidget.activeEffect()
    effect.self().ui.segmentationModelSelector.currentText = 'facial_nerve'
    effect.self().onClickSegmentation()
    facial_nerve = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("facial_nerve")
    segmentationNode.GetSegmentation().GetSegment(facial_nerve).SetColor(0.9,1,0)
    
    if exportlabelmaps==True:
      #Create labelmap for facial nerve and export the segment
      facial_labelmap = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, facial_labelmap, inputVolume)
      facial_labelmap.SetName('facial_labelmap')
      slicer.util.saveNode(facial_labelmap, directory+'/facial_labelmap.nrrd')

    if exportOBJ==True:
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      segnumber = shNode.GetItemByDataNode(segmentationNode)
      shNode.SetItemName(segnumber, volumeName+'_facial_nerve')
      segmentIDs = vtk.vtkStringArray()
      segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
      slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(directory,
        segmentationNode, segmentIDs, "OBJ", True,  1.0, False)

	#copy the facial nerve segment to another segmentation Node
    segmentationNode1.GetSegmentation().CopySegmentFromSegmentation(segmentationNode.GetSegmentation(),facial_nerve)
	
    # Remove the facial_nerve after exporting
    segmentationNode.GetSegmentation().RemoveSegment(facial_nerve)


    # Autosegmentation of Sigmoid sinus
    segmentEditorWidget.setActiveEffectByName("Nvidia AIAA")
    effect = segmentEditorWidget.activeEffect()
    effect.self().ui.segmentationModelSelector.currentText = 'sigmoid_sinus'
    effect.self().onClickSegmentation()
    sigmoid = segmentationNode.GetSegmentation().GetSegmentIdBySegmentName("sigmoid_sinus")
    segmentEditorWidget.setCurrentSegmentID(sigmoid)
    # Islands effect
    segmentEditorWidget.setActiveEffectByName("Islands")
    effect = segmentEditorWidget.activeEffect()
    effect.setParameter("Operation", 'REMOVE_SMALL_ISLANDS')
    effect.setParameter("MinimumSize", 500)
    effect.self().onApply()

    if exportlabelmaps==True:
      # Create labelmap for sigmoid sinus and export the segment
      sigmoid_labelmap = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLLabelMapVolumeNode')
      sigmoid_labelmap.SetName('sigmoid_labelmap')
      slicer.modules.segmentations.logic().ExportVisibleSegmentsToLabelmapNode(segmentationNode, sigmoid_labelmap, inputVolume)
      slicer.util.saveNode(sigmoid_labelmap, directory+'/sigmoid_labelmap.nrrd')

    if exportOBJ==True:
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      segnumber = shNode.GetItemByDataNode(segmentationNode)
      shNode.SetItemName(segnumber, volumeName+'_sigmoid')
      segmentIDs = vtk.vtkStringArray()
      segmentationNode.GetSegmentation().GetSegmentIDs(segmentIDs)
      slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(directory,
        segmentationNode, segmentIDs, "OBJ", True,  1.0, False)  

	#copy the sigmoid segment to another segmentation Node
    segmentationNode1.GetSegmentation().CopySegmentFromSegmentation(segmentationNode.GetSegmentation(),sigmoid)
	
    # Remove the sigmoid after exporting
    segmentationNode.GetSegmentation().RemoveSegment(sigmoid)

	# Remove the empty segmentation node
    slicer.mrmlScene.RemoveNode(segmentationNode)
	
	# Export the isotropic volume as nrrd file
    slicer.util.saveNode(inputVolume, directory+'/Volume.nrrd')

	# Export the isotropic volume as a DICOM series
    if exportDICOM==True:
      from datetime import datetime
      now = datetime.now()
      patient = now.strftime("%b-%d-%Y_%H-%M-%S")

      # Create patient and study and put the volume under the study
      shNode = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
      patientItemID = shNode.CreateSubjectItem(shNode.GetSceneItemID(), patient)
      studyItemID = shNode.CreateStudyItem(patientItemID, "Auto-segmentation Study")
      volumeShItemID = shNode.GetItemByDataNode(inputVolume)
      shNode.SetItemParent(volumeShItemID, studyItemID)

      import DICOMScalarVolumePlugin
      exporter = DICOMScalarVolumePlugin.DICOMScalarVolumePluginClass()
      exportables = exporter.examineForExport(volumeShItemID)
      for exp in exportables:
        exp.directory = directory

      exporter.export(exportables)

    # Make segmentation results visible in 3D
    segmentationNode1.CreateClosedSurfaceRepresentation()

    layoutManager = slicer.app.layoutManager()
    threeDWidget = layoutManager.threeDWidget(0)
    threeDView = threeDWidget.threeDView()
    threeDView.resetFocalPoint()
    
    # Remove volume 
    #slicer.mrmlScene.RemoveNode(median)

    #saveNode(inputVolume, directory+'/inputVolume.nrrd')
    #slicer.mrmlScene.RemoveNode(segmentationNode)
    #print(path)
    logging.info('Processing completed')
