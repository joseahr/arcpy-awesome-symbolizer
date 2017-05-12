# -*- coding: utf-8 -*-
import sys
import arcpy
import arcpy.mapping as mapping
from itertools import chain
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtGui import QMdiArea, QMdiSubWindow, QCheckBox
from functools import partial

#load form
form_class = uic.loadUiType("prac5entrega.ui")[0]

mxd = mapping.MapDocument(r'prac5entrega.mxd')

dataframe = mapping.ListDataFrames(mxd)[0]

layer = mapping.ListLayers(mxd,'',dataframe)[0]

symbolyr = arcpy.MakeFeatureLayer_management(layer)
fields = arcpy.ListFields(symbolyr)
fieldNames = map(lambda x : x.name, fields)
#print fieldNames

legendElement = mapping.ListLayoutElements(mxd, 'LEGEND_ELEMENT', 'legend')[0]
scaleElement = mapping.ListLayoutElements(mxd, 'MAPSURROUND_ELEMENT', 'scale_text')[0]

#print legendElement, scaleElement

#dialog class
class MyDialogClass(QtGui.QDialog, form_class):
    #init function
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self,parent)
        #init class dialog

        #run dialog
        self.setupUi(self)

        self.windows = [
              [self.combo_ts]
            , [self.combo_comp_t1, self.combo_comp_t2]
            , [self.combo_norm_c1, self.combo_norm_c2]
        ]

        self.checkboxes = [self.checkbox_ts, self.checkbox_vt, self.checkbox_norm]

        self.comboboxes = list(chain.from_iterable(self.windows))

        #print self.comboboxes

        [ combo.addItems(fieldNames) for combo in self.comboboxes ]

        self.mdiArea.setViewMode(QMdiArea.TabbedView)
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.windowOrder = QMdiArea.CreationOrder

        self.win_ts.setWindowTitle(u'Temático simple')
        self.win_vt.setWindowTitle(u'Comparación temáticos')
        self.win_norm.setWindowTitle(u'Normalización de campos (cociente)')

        self.mdiArea.addSubWindow(self.win_ts)
        self.mdiArea.addSubWindow(self.win_vt)
        self.mdiArea.addSubWindow(self.win_norm)

        self.txt_title.textChanged.connect(self.toggleBtnDo)

        self.btn_do.clicked.connect(self.do)

        [ check.stateChanged.connect(partial(self.checkboxChanged, check,  i)) for i, check in enumerate(self.checkboxes) ]
        [ check.setCheckState(2) for check in self.checkboxes ]
        [ check.setCheckState(0) for check in self.checkboxes ]

    def checkboxChanged(self, checkbox, windowID):
        enabled = checkbox.checkState() == 2
        [ combobox.setEnabled(enabled) for combobox in self.windows[windowID] ]
        self.toggleBtnDo()

    def toggleBtnDo(self):
        enabled_btn = any([ check.checkState() == 2 for check in self.checkboxes ]) and len(self.txt_title.text()) > 0
        self.btn_do.setEnabled(enabled_btn)
        num_maps = len([ check for check in self.checkboxes  if check.checkState() == 2 ])
        self.btn_do.setText('Imprimir mapas ({})'.format(num_maps))

    def do(self):
        title = self.txt_title.text()

        #if not self.check_scale.checkState() == 2 : scaleElement.delete()
        #if not self.check_legend.checkState() == 2: legendElement.delete()

        if self.checkbox_ts.checkState() == 2 :
            field = self.combo_ts.currentText()
            filename = '{}_ts_{}.pdf'.format(title, field)

            layer.symbology.valueField = field

            mapping.ExportToPDF(mxd, filename)

        if self.checkbox_vt.checkState() == 2 :
            fields = [ self.combo_comp_t1.currentText(), self.combo_comp_t2.currentText() ]

            filename = '{}_vt_{}.pdf'.format(title, fields[0])

            layer.symbology.valueField = field
            mapping.ExportToPDF(mxd, filename)

            filename = '{}_vt_{}.pdf'.format(title, fields[0])
            layer.symbology.valueField = field

            mapping.ExportToPDF(mxd, filename)

        if self.checkbox_ts.checkState() == 2 :
            fields = [ self.combo_norm_c1.currentText(), self.combo_norm_c2.currentText() ]

            filename = '{}_norm_{}_{}.pdf'.format(title, *fields)

            layer.symbology.valueField = fields[0]
            layer.symbology.normalization = self.combo_nc_2.currentText()
            layer.symbology.numClasses = 5

            mapping.ExportToPDF(mxd, filename)

app = QtGui.QApplication(sys.argv)
myDialog = MyDialogClass(None)
myDialog.show()
app.exec_()