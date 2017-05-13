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

#dialog class
class MyDialogClass(QtGui.QDialog, form_class):
    #init function
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self,parent)
        #init class dialog

        #run dialog
        self.setupUi(self)

        self.loadArcpyProjectSettings()

        self.windows = [
              [self.combo_ts]
            , [self.combo_comp_t1, self.combo_comp_t2]
            , [self.combo_norm_c1, self.combo_norm_c2]
        ]

        self.checkboxes = [self.checkbox_ts, self.checkbox_vt, self.checkbox_norm]

        self.comboboxes = list(chain.from_iterable(self.windows))

        #print self.comboboxes

        [ combo.addItems(self.fieldNames) for combo in self.comboboxes ]

        self.mdiArea.setViewMode(QMdiArea.TabbedView)
        self.mdiArea.setDocumentMode(True)
        self.mdiArea.windowOrder = QMdiArea.CreationOrder

        self.win_ts.setWindowTitle(u'Temático simple')
        self.win_vt.setWindowTitle(u'Comparación temáticos')
        self.win_norm.setWindowTitle(u'Normalización de campos (cociente)')

        self.mdiArea.addSubWindow(self.win_ts)
        self.mdiArea.addSubWindow(self.win_vt)
        self.mdiArea.addSubWindow(self.win_norm)

        '''
        window_ts = QMdiSubWindow()
        window_ts.setWidget(self.win_ts)
        window_vt = QMdiSubWindow(self.win_vt)
        window_vt.setWidget(self.win_vt)
        window_norm = QMdiSubWindow()
        window_norm.setWidget(self.win_norm)

        self.mdiArea.addSubWindow(window_ts)
        self.mdiArea.addSubWindow(window_vt)
        self.mdiArea.addSubWindow(window_norm)

        self.mdiArea.setActiveSubWindow(window_ts)
        '''


        self.txt_title.textChanged.connect(self.toggleBtnDo)

        self.btn_do.clicked.connect(self.do)

        [ check.stateChanged.connect(partial(self.checkboxChanged, check,  i)) for i, check in enumerate(self.checkboxes) ]
        [ check.setCheckState(2) for check in self.checkboxes ]
        [ check.setCheckState(0) for check in self.checkboxes ]


    def checkboxChanged(self, checkbox, windowID):
        enabled = checkbox.isChecked()
        [ combobox.setEnabled(enabled) for combobox in self.windows[windowID] ]
        self.toggleBtnDo()

    def toggleBtnDo(self):
        enabled_btn = any([ check.isChecked() for check in self.checkboxes ]) and len(self.txt_title.text()) > 0
        self.btn_do.setEnabled(enabled_btn)
        num_maps = len([ check for check in self.checkboxes  if check.isChecked() ])
        self.btn_do.setText('Imprimir mapas ({})'.format(num_maps))

    def do(self):
        title = str(self.txt_title.text())
        mapping.ListLayoutElements(self.mxd, 'TEXT_ELEMENT', 'title')[0].text = title
        #if not self.check_scale.isChecked() : scaleElement.delete()
        #if not self.check_legend.isChecked(): legendElement.delete()

        if self.checkbox_ts.isChecked() :
            field = self.combo_ts.currentText()
            filename = '{}_ts_{}.pdf'.format(title, field)

            self.layer.symbology.valueField = field

            mapping.ExportToPDF(self.mxd, filename)

        if self.checkbox_vt.isChecked() :
            fields = [ self.combo_comp_t1.currentText(), self.combo_comp_t2.currentText() ]

            filename = '{}_vt_{}.pdf'.format(title, fields[0])

            self.layer.symbology.valueField = fields[0]
            mapping.ExportToPDF(self.mxd, filename)

            filename = '{}_vt_{}.pdf'.format(title, fields[1])
            self.layer.symbology.valueField = fields[1]

            mapping.ExportToPDF(self.mxd, filename)

        if self.checkbox_norm.isChecked() :
            fields = [ self.combo_norm_c1.currentText(), self.combo_norm_c2.currentText() ]

            filename = '{}_norm_{}_{}.pdf'.format(title, *fields)

            self.layer.symbology.valueField = fields[0]
            self.layer.symbology.normalization = fields[1]
            self.layer.symbology.numClasses = 5

            mapping.ExportToPDF(self.mxd, filename)

        del self.mxd
        self.loadArcpyProjectSettings()
        self.txt_title.setText('')
        print 'doneee'


    def loadArcpyProjectSettings(self):
        self.mxd = mapping.MapDocument(r'prac5entrega.mxd')

        self.dataframe = mapping.ListDataFrames(self.mxd)[0]

        self.layer = mapping.ListLayers(self.mxd, '', self.dataframe)[0]

        self.layer_lyr = arcpy.MakeFeatureLayer_management(self.layer)
        self.fields = arcpy.ListFields(self.layer_lyr)
        self.fieldNames = map(lambda x: x.name, self.fields)
        # print fieldNames

        self.legendElement = mapping.ListLayoutElements(self.mxd, 'LEGEND_ELEMENT', 'legend')[0]
        self.scaleElement = mapping.ListLayoutElements(self.mxd, 'MAPSURROUND_ELEMENT', 'scale_text')[0]
        # print legendElement, scaleElement
        #print self.layer.symbologyType

app = QtGui.QApplication(sys.argv)
myDialog = MyDialogClass(None)
myDialog.show()
app.exec_()