# -*- coding: utf-8 -*-
import sys
import arcpy
import arcpy.mapping as mapping
from os import path
from multiprocessing import Process
from itertools import chain
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog, QMessageBox
from functools import partial

# Se carga el formulario mediante la herramienta UIC
# Esto comvierte el formulario XML diseñado en QT designer
# en código Python. También se puede usar el ejecutable uic
# para utilizarlo en la línea de comandos
form_class = uic.loadUiType("prac5entrega.ui")[0]

# Clase diálogo - Hereda las propiedades de QDialog
# y el formulario generado del XML
class MyDialogClass(QtGui.QDialog, form_class):

    # Constructor
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self,parent)

        # Inicialización del dialog
        # Como llamar al constructor de la clase QDialog
        self.setupUi(self)

        # Título del mapa
        self.title = ''

        # Información extra en los paths de salida
        self.append_info = ''

        # Creamos una lista que almacenará
        # los comboboxes de cada ventana
        self.windows = [
              [self.combo_ts]
            , [self.combo_comp_t1, self.combo_comp_t2]
            , [self.combo_norm_c1, self.combo_norm_c2]
        ]

        # CheckBoxes que controlan los comboboxes de cada ventana
        # Ordenados en el orden con la lista self.windows,
        self.checkboxes = [self.checkbox_ts, self.checkbox_vt, self.checkbox_norm]

        # Todos los comboboxes en un lista (Flattened)
        self.comboboxes = list(chain.from_iterable(self.windows))

        # Carpeta donde se guardarán los PDFs
        self.export_folder = '.'

        # Ponemos activa la primera TAB
        self.tabs.setCurrentIndex(0)

        # Conectamos los eventos con las funciones
        self.txt_title.textChanged.connect(self.toggleBtnDo) #Título del mapa
        self.btn_do.clicked.connect(self.do) # Botón proceso
        self.btn_load_shp.clicked.connect(self.getFile) # Botón MXD
        self.btn_select_folder.clicked.connect(self.getResultFolder) # Botón Carpeta exportar
        [
            check.stateChanged.connect(partial(self.checkboxChanged, check,  i)) \
            for i, check in enumerate(self.checkboxes) # Eventos Checkbox -- Activar/Desactivar comboboxes
        ]

        '''
        [ check.setCheckState(2) for check in self.checkboxes ] # Checkeamos los checboxes - Si no al ya estar checkeados no cambia
        [ check.setCheckState(0) for check in self.checkboxes ] # Descheckeamos los checkboxes - Ahora se desactivarán también los combos
        [ check.setEnabled(False) for check in self.checkboxes ] # Desactivamos los checkboxes hasta que se añada un MXD
        '''

    def checkboxChanged(self, checkbox, windowID):
        '''
        @param: self
        @brief: Activa/Desactiva comboboxes en función del estado del checkbox pasado
        @return: None
        '''
        enabled = checkbox.isChecked()
        # Activamos/Desactivamos los comboboxes de la ventana
        [ combobox.setEnabled(enabled) for combobox in self.windows[windowID] ]
        # Llamamos a la función toggleBtnDo para activar el botón que ejecuta el proceso
        # al hacer click si el formulario cumple la validación
        self.toggleBtnDo()

    def toggleBtnDo(self):
        '''
        @param: self
        @brief: Activa/Desactiva el botón que ejecuta el proceso
                al hacer click si el formulario cumple la validación
        @return: None
        '''
        # Estará activo si algún checbox de alguna ventana está marcado
        # Y se ha puesto algo como título
        enabled_btn = any([ check.isChecked() for check in self.checkboxes ]) and len(self.txt_title.text()) > 0
        self.btn_do.setEnabled(enabled_btn)
        # Actualizamos también el texto del botón para reflejar el número de mapas
        # a imprimir
        num_maps = len([ check for check in self.checkboxes  if check.isChecked() ])
        self.btn_do.setText('Imprimir mapas ({})'.format(num_maps))


    def checkScaleBefore(self):
        '''
        @param: self
        @brief: Oculta las escalas
        @return: None
        '''
        self.dataframe1_scaletext.elementPositionX += 100
        self.dataframe2_scaletext.elementPositionX += 100

        self.dataframe1_scalebar.elementPositionX += 100
        self.dataframe2_scalebar.elementPositionX += 100

    def checkScaleAfter(self):
        '''
        @param: self
        @brief: Vuelve a poner las escalas en su sitio
        @return: None
        '''
        self.dataframe1_scaletext.elementPositionX -= 100
        self.dataframe2_scaletext.elementPositionX -= 100

        self.dataframe1_scalebar.elementPositionX -= 100
        self.dataframe2_scalebar.elementPositionX -= 100

    def checkLegendBefore(self):
        '''
        @param: self
        @brief: Oculta las leyendas
        @return: None
        '''
        self.legend_title.elementPositionX += 100
        self.legend_df1.elementPositionX += 100
        self.legend_df2.elementPositionX += 100

    def checkLegendAfter(self):
        '''
        @param: self
        @brief: Vuelve a poner las leyendas en su sitio
        @return: None
        '''
        self.legend_title.elementPositionX -= 100
        self.legend_df1.elementPositionX -= 100
        self.legend_df2.elementPositionX -= 100

    def checkDataFrameNames(self):
        '''
        @param: self
        @brief: Asigna el nuevo nombre a los dataframes
        @return: None
        '''
        df1name = str(self.line_edit_df_1.text())
        df2name = str(self.line_edit_df_2.text())

        if not self.dataframes[0].name == df1name:
            self.dataframes[0].name = df1name

        if not self.dataframes[1].name == df2name:
            self.dataframes[1].name = df2name

    def doTematicoSimple(self):
        '''
        @param: self
        @brief: Realiza el mapa temático simple
        @return: None
        '''
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth += self.legend_df1.elementWidth

        field = self.combo_ts.currentText()
        filename = path.join(self.export_folder, '{}_ts_{}_{}.pdf'.format(self.title, '_'.join(self.append_info), field))

        self.layer.symbology.valueField = field

        mapping.ExportToPDF(self.mxd, filename)

        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth -= self.legend_df1.elementWidth

    def doVariosTematicos(self):
        '''
        @param: self
        @brief: Realiza el mapa con varios temáticos
        @return: None
        '''
        self.setTwoDataFrameMode()
        fields = [self.combo_comp_t1.currentText(), self.combo_comp_t2.currentText()]

        filename = path.join(self.export_folder, '{}_vt_{}_{}_{}.pdf'.format(title, '_'.join(append_info), *fields))

        self.layer.symbology.valueField = fields[0]
        layer_df2 = self.layers[1][0]
        layer_df2.symbology.valueField = fields[1]
        mapping.ExportToPDF(self.mxd, filename)

        self.setOneDataFrameMode()

    def doNormalizacion(self):
        '''
        @param: self
        @brief: Realiza el mapa de normalización
        @return: None
        '''
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth += self.legend_df1.elementWidth
        fields = [self.combo_norm_c1.currentText(), self.combo_norm_c2.currentText()]

        filename = path.join(self.export_folder, '{}_norm_{}_{}_{}.pdf'.format(title, '_'.join(append_info), *fields))

        self.layer.symbology.valueField = fields[0]
        self.layer.symbology.normalization = fields[1]
        self.layer.symbology.numClasses = 5

        mapping.ExportToPDF(self.mxd, filename)
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth -= self.legend_df1.elementWidth

        # Ponemos normalización igual a None
        # Así no afectará a próximos mapas
        self.layer.symbology.normalization = None

    def do(self):
        '''
        @param: self
        @brief: Realiza todo el proceso en función de lo seleccionado en el formulario
        @return: None
        '''
        # Añadimos el título al mapa
        # El título es añadido por el usuario en un LineEDIT
        self.title = str(self.txt_title.text())
        self.map_title.text = self.title

        # Información extra en la ruta de los PDFs de salida
        self.append_info = []

        # Si el check de escala no está activado
        if not self.check_scale.isChecked() :
            # Movemos todo lo que tenga que ver con la escala
            # en el Layout fuera de este
            # Añadimos al path de salida 'no-scale'
            self.checkScaleBefore()
            self.append_info.append('no-scale')

        # Si el check de leyenda no está activado
        if not self.check_legend.isChecked():
            # Movemos todo lo que tenga que ver con la leyenda
            # en el Layout fuera de este
            # Añadimos al path de salida 'no-legend'
            self.checkLegendBefore()
            self.append_info.append('no-legend')

        # Si el usuario ha cambiado el nombre de los
        # dataframes, actualizamos los nombres
        self.checkDataFrameNames()

        # Ponemos el mapa en modo "Single-DataFrame"
        # Moviendo el segundo DF fuera del Layout
        self.setOneDataFrameMode()

        # Si el check de TS está marcado realizamos el mapa TS
        if self.checkbox_ts.isChecked() : self.doTematicoSimple()
        # Si el check de VT está marcado realizamos el mapa VT
        if self.checkbox_vt.isChecked() : self.doVariosTematicos()
        # Si el check de NORM está marcado realizamos el mapa NORM
        if self.checkbox_norm.isChecked() : self.doNormalizacion()

        # Ponemos la escala donde estaba si la hemos movido
        if not self.check_scale.isChecked():
            self.checkScaleAfter()
        # Ponemos la leyenda donde estaba si la hemos movido
        if not self.check_legend.isChecked():
            self.checkLegendAfter()

        # Finalizamos dejando el mapa en estado "Two-DataFrames"
        # el cual es el que viene por defecto en nuestro MXD
        self.setTwoDataFrameMode()

        # Reinicializamos el LineEDIT del título
        self.txt_title.setText('')

        # Mostramos un mensaje de INFO - Todo bien, todo correcto
        QMessageBox.information(self, 'Fin del proceso', 'Mapa/s exportado/s correctamente')

    def setOneDataFrameMode(self):
        '''
        @param: self
        @brief: Oculta todo lo relacionado con el DF2
                y hace ocupar todo el ancho a lo relacionado con el DF1
        @return: None
        '''
        self.dataframe2_scaletext.elementPositionX += 100
        self.dataframe1_scalebar.elementPositionX += 10
        self.dataframe2_scalebar.elementPositionX += 100

        self.legend_title.elementPositionX += 10
        self.legend_df1.elementPositionX += 10
        self.legend_df2.elementPositionX += 100

        self.dataframe1.elementWidth += 10
        self.dataframe2.elementPositionX += 100

    def setTwoDataFrameMode(self):
        '''
        @param: self
        @brief: Deshace lo hecho por la función setOneDataFrameMode
        @return: None
        '''
        self.dataframe2_scaletext.elementPositionX -= 100
        self.dataframe1_scalebar.elementPositionX -= 10
        self.dataframe2_scalebar.elementPositionX -= 100

        self.legend_title.elementPositionX -= 10
        self.legend_df1.elementPositionX -= 10
        self.legend_df2.elementPositionX -= 100

        self.dataframe1.elementWidth -= 10
        self.dataframe2.elementPositionX -= 100

    def getResultFolder(self):
        '''
        @param: self
        @brief: Obtiene el directorio de salida para los PDFs
        @return: None
        '''
        foldername = str(QFileDialog.getExistingDirectory(self, "Select Directory"))

        if not foldername : return

        self.export_folder = foldername
        self.label_selected_folder.setText(self.export_folder)
        print self.export_folder

    def getFile(self):
        '''
        @param: self
        @brief: Obtiene los datos del MXD seleccionado
        @return: None
        '''
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

            self.txt_title.setEnabled(True)
            self.check_scale.setEnabled(True)
            self.check_legend.setEnabled(True)
            self.line_edit_df_1.setEnabled(True)
            self.line_edit_df_2.setEnabled(True)

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