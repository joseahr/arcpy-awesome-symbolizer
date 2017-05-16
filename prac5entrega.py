# -*- coding: utf-8 -*-
import sys
import arcpy
import arcpy.mapping as mapping
from os import path
from itertools import chain
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog
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

        self.windows = [
              [self.combo_ts]
            , [self.combo_comp_t1, self.combo_comp_t2]
            , [self.combo_norm_c1, self.combo_norm_c2]
        ]

        self.export_folder = '.'

        self.checkboxes = [self.checkbox_ts, self.checkbox_vt, self.checkbox_norm]

        self.comboboxes = list(chain.from_iterable(self.windows))

        #print self.comboboxes

        self.tabs.setCurrentIndex(0)

        self.txt_title.textChanged.connect(self.toggleBtnDo)
        self.btn_do.clicked.connect(self.do)
        self.btn_load_shp.clicked.connect(self.getFile)
        self.btn_select_folder.clicked.connect(self.getResultFolder)

        [ check.stateChanged.connect(partial(self.checkboxChanged, check,  i)) for i, check in enumerate(self.checkboxes) ]
        [ check.setCheckState(2) for check in self.checkboxes ]
        [ check.setCheckState(0) for check in self.checkboxes ]
        [ check.setEnabled(False) for check in self.checkboxes ]


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

        append_info = []
        if not self.check_scale.isChecked() :
            self.dataframe1_scaletext.elementPositionX += 100
            self.dataframe2_scaletext.elementPositionX += 100

            self.dataframe1_scalebar.elementPositionX += 100
            self.dataframe2_scalebar.elementPositionX += 100
            append_info.append('no-scale')
        if not self.check_legend.isChecked():
            self.legend_title.elementPositionX += 100
            self.legend_df1.elementPositionX += 100
            self.legend_df2.elementPositionX += 100
            append_info.append('no-legend')

        df1name = str(self.line_edit_df_1.text())
        df2name = str(self.line_edit_df_2.text())

        if not self.dataframes[0].name == df1name:
            self.dataframes[0].name = df1name

        if not self.dataframes[1].name == df2name:
            self.dataframes[1].name = df2name

        self.map_title.text = title

        self.setOneDataFrameMode()

        if self.checkbox_ts.isChecked() :
            if not self.check_legend.isChecked():
                self.dataframe1.elementWidth += self.legend_df1.elementWidth
            field = self.combo_ts.currentText()
            filename = path.join(self.export_folder, '{}_ts_{}_{}.pdf'.format(title, '_'.join(append_info), field))

            self.layer.symbology.valueField = field

            mapping.ExportToPDF(self.mxd, filename)
            if not self.check_legend.isChecked():
                self.dataframe1.elementWidth -= self.legend_df1.elementWidth

        if self.checkbox_vt.isChecked() :
            self.setTwoDataFrameMode()
            fields = [ self.combo_comp_t1.currentText(), self.combo_comp_t2.currentText() ]

            filename = path.join(self.export_folder, '{}_vt_{}_{}_{}.pdf'.format(title, '_'.join(append_info), *fields))

            self.layer.symbology.valueField = fields[0]
            layer_df2 = self.layers[1][0]
            layer_df2.symbology.valueField = fields[1]
            mapping.ExportToPDF(self.mxd, filename)

            self.setOneDataFrameMode()

        if self.checkbox_norm.isChecked() :
            if not self.check_legend.isChecked():
                self.dataframe1.elementWidth += self.legend_df1.elementWidth
            fields = [ self.combo_norm_c1.currentText(), self.combo_norm_c2.currentText() ]

            filename = path.join(self.export_folder, '{}_norm_{}_{}_{}.pdf'.format(title, '_'.join(append_info), *fields))

            self.layer.symbology.valueField = fields[0]
            self.layer.symbology.normalization = fields[1]
            self.layer.symbology.numClasses = 5

            mapping.ExportToPDF(self.mxd, filename)
            if not self.check_legend.isChecked():
                self.dataframe1.elementWidth -= self.legend_df1.elementWidth

        if not self.check_scale.isChecked():
            self.dataframe1_scaletext.elementPositionX -= 100
            self.dataframe2_scaletext.elementPositionX -= 100

            self.dataframe1_scalebar.elementPositionX -= 100
            self.dataframe2_scalebar.elementPositionX -= 100
        if not self.check_legend.isChecked():
            self.legend_title.elementPositionX -= 100
            self.legend_df1.elementPositionX -= 100
            self.legend_df2.elementPositionX -= 100

        self.setTwoDataFrameMode()

        self.txt_title.setText('')
        print 'doneee'

        self.layer.symbology.normalization = None

    def setOneDataFrameMode(self):

        self.dataframe2_scaletext.elementPositionX += 100
        self.dataframe1_scalebar.elementPositionX += 10
        self.dataframe2_scalebar.elementPositionX += 100

        self.legend_title.elementPositionX += 10
        self.legend_df1.elementPositionX += 10
        self.legend_df2.elementPositionX += 100

        self.dataframe1.elementWidth += 10
        self.dataframe2.elementPositionX += 100

    def setTwoDataFrameMode(self):
        self.dataframe2_scaletext.elementPositionX -= 100
        self.dataframe1_scalebar.elementPositionX -= 10
        self.dataframe2_scalebar.elementPositionX -= 100

        self.legend_title.elementPositionX -= 10
        self.legend_df1.elementPositionX -= 10
        self.legend_df2.elementPositionX -= 100

        self.dataframe1.elementWidth -= 10
        self.dataframe2.elementPositionX -= 100

    def getResultFolder(self):
        foldername = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if not foldername : return

        self.export_folder = foldername
        self.label_selected_folder.setText(self.export_folder)
        print self.export_folder

    def getFile(self):
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        dlg.setFilter("shapefile (*.mxd)")

        if dlg.exec_():
            filepath = map(str, list(dlg.selectedFiles()))[0]
            self.mxd = mapping.MapDocument(filepath)
            self.dataframes = mapping.ListDataFrames(self.mxd)
            self.layers = map(lambda dataframe : mapping.ListLayers(self.mxd, None, dataframe), self.dataframes)
            self.layer = self.layers[0][0]

            fieldnames = map( lambda x : x.name, arcpy.ListFields(self.layer.dataSource) )
            #print fieldnames

            [combo.addItems(fieldnames) for combo in self.comboboxes]
            #print self.mxd, self.dataframes, self.layers

            [check.setEnabled(True) for check in self.checkboxes]

            self.label_mxd_path.setText(filepath)
            self.line_edit_df_1.setText(self.dataframes[0].name)
            self.line_edit_df_2.setText(self.dataframes[1].name)

            self.dataframe1_scalebar = mapping.ListLayoutElements(self.mxd, '', 'data-frame-1-scale-bar')[0]
            self.dataframe1_scaletext = mapping.ListLayoutElements(self.mxd, '', 'data-frame-1-scale-text')[0]
            self.dataframe2_scalebar = mapping.ListLayoutElements(self.mxd, '', 'data-frame-2-scale-bar')[0]
            self.dataframe2_scaletext = mapping.ListLayoutElements(self.mxd, '', 'data-frame-2-scale-text')[0]

            self.legend_title = mapping.ListLayoutElements(self.mxd, '', 'legend-title')[0]
            self.legend_df1 = mapping.ListLayoutElements(self.mxd, '', 'legend-df-1')[0]
            self.legend_df2 = mapping.ListLayoutElements(self.mxd, '', 'legend-df-2')[0]

            self.map_title = mapping.ListLayoutElements(self.mxd, 'TEXT_ELEMENT', 'title')[0]

            self.dataframe1 = mapping.ListLayoutElements(self.mxd, '', 'data-frame-1')[0]
            self.dataframe2 = mapping.ListLayoutElements(self.mxd, '', 'data-frame-2')[0]

app = QtGui.QApplication(sys.argv)
myDialog = MyDialogClass(None)
myDialog.show()
app.exec_()