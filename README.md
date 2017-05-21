![Formulario](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_exe.png)

# Índice
***

- [Introducción y objetivos](#introducción-y-objetivos)
    - [¿Porqué este flujo de trabajo?](#porqué-este-flujo-de-trabajo)
    - [Herramientas utilizadas](#herramientas-utilizadas)
    - [Desarrollo del formulario PyQt4 mediante Qt Designer](#desarrollo-del-formulario-pyqt4-mediante-qt-designer)
- [Desarrollo de la práctica](#desarrollo-de-la-práctica)
- [Resultados](#resultados)
- [Conclusiones](#conclusiones)

# Introducción y Objetivos
***

El objetivo del presente documento es mostrar el trabajo realizado en la elaboración de una herramienta para realizar mapas temáticos dependiendo de distintas opciones.

Utilizaremos para construir la interfaz gráfica *`PyQt4`*, un binding de la librería ``Qt`` escrita en ``C++``, para ``python``.

El **flujo de trabajo** de la aplicación será:

- Leer el fichero ``.mxd`` que contendrá dos layouts, diseño del mapa, etc.
- Leer archivo ``.lyr`` que contendrá la simbología ``GRADUATED_COLORS`` (Este es obtenido a partir de una capa en el entorno de escritorio de ArcGIS)
- El usuario seleccionará un archivo ``.shp``, la capa será añadida a los ``dataframes`` y se le aplicará la simbología ``GRADUATED_COLORS``.
- El usuario podrá seleccionar ``qué temáticos desea exportar``, así como el ``nombre de los dataframes`` y la carpeta donde desea que se guarden los documentos ``.pdf`` generados.

## ¿Porqué este flujo de trabajo?

Existen [**limitaciones**](http://help.arcgis.com/en/arcgisdesktop/10.0/help/index.html#//00s30000006s000000) a la hora de utilizar ``arcpy`` (en concreto ``arcpy.mapping``) que hay que tener en cuenta en esta práctica:

- No podemos generar desde ``arcpy`` proyectos de ArcMap (``.mxd``)
- No podemos crear una capa de simbología ``lyr`` a partir de un shapefile seleccionado. Hay que crear manualmente un archivo ``.lyr`` con la simbología deseado desde **ArcMap** y utilizar ``arcpy.mapping.UpdateLayer`` o ``arcpy.ApplySymbologyFromLayer_management`` para actualizar la simbología de una capa que añadimos al dataframe. Es decir:
```python
if layer.symbologyType == u'OTHER':
    assert layer.symbology == None
```
Y al ser ``symbology`` una propiedad de ``solo lectura`` (**readonly**) no podemos modificarla. Lo ideal sería poder hacer:
```python
layer.symbology = GraduatedColorsSymbology()
...
layer.symbology = AnotherSymbologyClass()
```

Esto sigue siendo así incluso en [nuevas versiones](http://desktop.arcgis.com/es/arcmap/latest/analyze/arcpy-mapping/introduction-to-arcpy-mapping.htm#ESRI_SECTION1_B482E78268684B728BFF0636AAFF40FD):

> ``Arcpy.mapping`` is not a replacement for ``ArcObjects`` but rather an alternative for the different scenarios it supports. ArcObjects is still necessary for finer-grain development and application customization, whereas ``arcpy.mapping`` **is intended for automating the contents of existing map documents and layer files**.

> ``Arcpy.mapping`` no es un reemplazamiento de ``ArcObjects`` pero una alternativa en los escenarios que soporta. ``ArcObjects`` sigue siendo necesario para un desarrollo más refinado y una aplicación más personalizada, mientras que ``arcpy.mapping`` **pretende automatizar los contenidos de documentos de mapa o archivos de capa existentes.**.

### Herramientas utilizadas

 - ArcMap 10.1 
 - Python 2.7 (``arcpy``, ``arcpy.mapping``, ``PyQt4``)

### Módulos de python utilizados

Estos son los módulos utilizados para desarrollar la herramienta:
```python
from __future__ import unicode_literals
import sys
import arcpy
import arcpy.mapping as mapping
import math
from os import path
from itertools import chain
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog, QMessageBox
from functools import partial
```

Una cosa importante a tener en cuenta en las declaraciones ``import`` es no sobreescribir funciones [built-in](https://docs.python.org/2/library/functions.html#built-in-functions) de python:

```python
import arcpy.mapping as map
```

El código anterior es una mala práctica, ya que estamos sobreescribiendo la función [map](https://docs.python.org/2/library/functions.html#map) que viene por defecto en python y puede inducir a problemas e **inconsistencias** en nuestro código.

 
### Desarrollo del formulario PyQt4 mediante Qt Designer

El desarrollo del formulario se ha llevado a cabo utilizando **Qt Designer**, una herramienta para crear formularios de forma interactiva para **Qt**. **Qt** generará un archivo ``.ui``, un archivo ``XML`` que mapea los componentes que hemos utilizado en nuestro formulario.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<ui version="4.0">
 <class>Dialog</class>
 <widget class="QDialog" name="Dialog">
  <property name="geometry">
   <rect>
   ...
   </rect>
  </property>
  ...
 </widget>
</ui>
```

Con este archivo podemos hacer dos cosas:
- Utilizar le herramienta de línea de comandos llamada ``uic`` y que viene en la carpeta ``bin`` dentro de la instalación de ``PyQt4``, que generará un archivo ``.py`` con la inicialización de los componentes de nuestro formulario.
- Utilizar el ``módulo uic`` de ``PyQt4`` dentro de nuestro código, el cual generará también el **correspondiente código de python de nuestro formulario**, para utilizarlo dentro de nuestro código. Se ha escogido esta opción pese a ser más lenta, ya que resulta más intuitiva para el aprendizaje.

# Desarrollo de la práctica
***
 
En primer lugar se ha llevado a cabo el formulario usando **Qt Designer**. 

Componentes del formulario:
- ``QLineEdit`` para el título del mapa
- ``QCheckBox`` para la escala y la leyenda
- ``QTabWidget`` con los siguientes QTabs:
    - ``QTab`` para temático simple:
        - ``QCombobox`` para el campo
    - ``QTab`` para varios temáticos:
        - ``QCombobox`` para el campo 1
        - ``QCombobox`` para el campo 2
    - ``QTab`` para normalización de campos:
        - ``QCombobox`` para el campo 1
        - ``QCombobox`` para el campo 2
    - ``QTab`` para elegir el nombre de los dataframes:
        - ``QLineEdit`` para nombre del primer dataframe
        - ``QLineEdit`` para nombre del segundo dataframe
    - ``QTab`` para elegir la carpeta de salida:
        - ``QPushButton`` para elegir la carpeta de salida
        - ``QScrollArea`` para añadir un label con la ruta de la carpeta de salida
- ``QScrollArea`` para mostrar la ruta del archivo ``.shp`` dentro de un ``QLabel``.
- ``QPushButton`` para elegir el archivo ``.shp``
- ``QPushButton`` para realizar el proceso de impresión

También hacemos que algunos componentes (``QCombobox``, ``QCheckBox``, ``...``) no estén activos al iniciar el formulario.

![Temático Simple](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_ts.PNG)

![Varios Temáticos](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_vt.PNG)

![Normalización de campos (cociente)](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_norm.PNG)

![Nombre dataframes](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_df_name.PNG)

![Seleccionar carpeta de salida](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_select_folder.PNG)

Los botones para seleccionar ``.shp`` y seleccionar ``la carpeta de salida`` abrirán los siguientes diálogos respectivamente:

![Seleccionar shapefile](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_selec_shp.png)

![Seleccionar carpeta de salida](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_selec_dir.png)

Si el proceso de exportación de los archivos ``.pdf`` no finaliza con errores mostraremos un mensaje de información:

![Mensaje Success](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/form_success_msg.png)


Una vez realizado el formulario, pasamos a crear todo el material necesario para el funcionamiento de la aplicación a partir de **ArcMap**, es decir:

- ``Archivo .mxd``: Contendrá los dataframes, diseño del mapa, etc...
- ``Archivo .lyr (Graduated Colors)``: Contendrá la simbología de tipo **GRADUATED_COLORS**.

![Mensaje Success](https://raw.githubusercontent.com/joseahr/arcpy-awesome-symbolizer/master/images/map_design.PNG)

Con todo esto podemos empezar a implementar la lógica de funcionamiento de nuestra aplicación. El código se muestra (**comentado**) a continuación:

```python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import sys
import arcpy
import arcpy.mapping as mapping
import math
from os import path
from itertools import chain
from PyQt4 import QtGui, uic
from PyQt4.QtGui import QFileDialog, QMessageBox
from functools import partial
# Se carga el formulario mediante la herramienta UIC
# Esto comvierte el formulario XML diseñado en QT designer
# en código Python. También se puede usar el ejecutable uic
# para utilizarlo en la línea de comandos
form_class = uic.loadUiType("awesome-symbolizer.ui")[0]

# Ruta del fichero MXD del proyecto
# Aquí estarán los 2 DataFrames necesarios
MXD_PATH = 'dummymxd.mxd'

# Ruta del fichero LYR que contiene la simbología
# GRADUATED COLORS --> assert layer.symbologyType == 'GRADUATED COLORS'
GRADUATED_COLORS_LYR_PATH = 'graduated_colors.lyr'

# Clase diálogo - Hereda las propiedades de QDialog
# y el formulario generado del XML
class MyDialogClass(QtGui.QDialog, form_class):

    # Constructor
    def __init__(self, parent = None):
        QtGui.QDialog.__init__(self,parent)

        # Inicialización del dialog
        # Como llamar al constructor de la clase QDialog
        self.setupUi(self)

        # Modo del Layout --> 1 (1 solo Layout/DataFrame), 2 --> (2 Layouts/DataFrame)
        self.mode = 2

        # Título del mapa
        self.title = ''

        # Carpeta donde se guardarán los PDFs
        self.export_folder = '.'

        # Información extra en los paths de salida
        self.append_info = []

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

        # Ponemos activa la primera TAB
        self.tabs.setCurrentIndex(0)

        # Conectamos los eventos con las funciones
        self.txt_title.textChanged.connect(self.toggleBtnDo) #Título del mapa
        self.btn_do.clicked.connect(self.do) # Botón proceso
        self.btn_load_shp.clicked.connect(self.getFile) # Botón MXD
        self.btn_select_folder.clicked.connect(self.getResultFolder) # Botón Carpeta exportar
        [
            ## La función partial es similar a #Function.prototype.bind en EcmaScript
            ## Es decir devuelve una nueva función a partir de la función dada
            ## A la que podemos asignar los argumentos de entrada
            ## Si quisiéramos asignarle kwargs también se podría
            check.stateChanged.connect(partial(self.checkboxChanged, check,  i)) \
            for i, check in enumerate(self.checkboxes) # Eventos Checkbox -- Activar/Desactivar comboboxes
        ]

        # Cargamos el MXD
        self.loadMXD()
        # Cargamos el LYR
        self.loadLYR()

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

        # No usar str() para convertir de unicode a encoded text/bytes
        # http://stackoverflow.com/questions/9942594/unicodeencodeerror-ascii-codec-cant-encode-character-u-xa0-in-position-20
        # http://stackoverflow.com/a/19198328/3866134
        # https://es.stackoverflow.com/a/68868/6095
        # En python 3 no existe este problema, python 3 maneja esto por nosotros
        #df1name = str(self.line_edit_df_1.text())
        df1name = unicode(self.line_edit_df_1.text())
        df2name = unicode(self.line_edit_df_2.text())

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

        # Si está en modo (2 Layouts), pasamos a modo (1 Layout)
        if self.mode == 2: self.setOneDataFrameMode()

        layer_df1, _ = self.layers

        # Hacemos que el DF ocupe todo el ancho si no hay leyenda
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth += self.legend_df1.elementWidth

        field = self.combo_ts.currentText()
        filename = path.join(
            self.export_folder
            , '{}_ts_{}_{}.pdf'.format(self.title, '_'.join(self.append_info), field)
        )

        layer_df1.symbology.valueField = field
        print 'TS Break Values', layer_df1.symbology.classBreakValues

        #layer_df1.symbology.classBreakValues = self.normalizeBreakValues(layer_df1.symbology.classBreakValues)
        #self.GRADUATED_COLORS.symbology.valueField = field
        #arcpy.ApplySymbologyFromLayer_management(layer_df1, self.GRADUATED_COLORS)

        mapping.ExportToPDF(self.mxd, filename)

        # Volvemos a hacer que el dataframe ocupe el ancho original
        # si no hay leyenda
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth -= self.legend_df1.elementWidth

    def doVariosTematicos(self):
        '''
        @param: self
        @brief: Realiza el mapa con varios temáticos
        @return: None
        '''
        if self.mode == 1: self.setTwoDataFrameMode()

        layer_df1, layer_df2 = self.layers

        fields = [self.combo_comp_t1.currentText(), self.combo_comp_t2.currentText()]

        filename = path.join(
            self.export_folder,
            '{}_vt_{}_{}_{}.pdf'.format(self.title, '_'.join(self.append_info), *fields)
        )

        layer_df1.symbology.valueField = fields[0]
        layer_df2.symbology.valueField = fields[1]
        print 'VT Break Values', layer_df1.symbology.classBreakValues
        print 'VT Break Values', layer_df2.symbology.classBreakValues
        #layer_df1.symbology.classBreakValues = self.normalizeBreakValues(layer_df1.symbology.classBreakValues)
        #layer_df2.symbology.classBreakValues = self.normalizeBreakValues(layer_df2.symbology.classBreakValues)
        mapping.ExportToPDF(self.mxd, filename)

    def doNormalizacion(self):
        '''
        @param: self
        @brief: Realiza el mapa de normalización
        @return: None
        '''

        if self.mode == 2: self.setOneDataFrameMode()

        layer_df1, _ = self.layers

        # Hacemos que el DF ocupe todo el ancho si no hay leyenda
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth += self.legend_df1.elementWidth

        fields = [self.combo_norm_c1.currentText(), self.combo_norm_c2.currentText()]

        filename = path.join(
            self.export_folder,
            '{}_norm_{}_{}_{}.pdf'.format(self.title, '_'.join(self.append_info), *fields)
        )

        layer_df1.symbology.valueField = fields[0]
        layer_df1.symbology.normalization = fields[1]
        #layer_df1.symbology.numClasses = 5
        print 'NORM Break Values', layer_df1.symbology.classBreakValues
        #layer_df1.symbology.classBreakValues = self.normalizeBreakValues(layer_df1.symbology.classBreakValues)
        mapping.ExportToPDF(self.mxd, filename)

        # Ponemos normalización igual a None
        # Así no afectará a próximos mapas
        layer_df1.symbology.normalization = None

        # Volvemos a hacer que el dataframe ocupe el ancho original
        # si no hay leyenda
        if not self.check_legend.isChecked():
            self.dataframe1.elementWidth -= self.legend_df1.elementWidth

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
        self.mode = 1
        self.dataframe2_scaletext.elementPositionX += 100
        self.dataframe1_scalebar.elementPositionX += 10
        self.dataframe2_scalebar.elementPositionX += 100

        self.legend_title.elementPositionX += 10
        self.legend_df1.elementPositionX += 10
        self.legend_df2.elementPositionX += 100

        print 'd1 width', self.dataframe1.elementWidth
        self.dataframe1.elementWidth += 10
        print 'd1 width', self.dataframe1.elementWidth
        self.dataframe2.elementPositionX += 100

    def setTwoDataFrameMode(self):
        '''
        @param: self
        @brief: Deshace lo hecho por la función setOneDataFrameMode
        @return: None
        '''
        self.mode = 2
        self.dataframe2_scaletext.elementPositionX -= 100
        self.dataframe1_scalebar.elementPositionX -= 10
        self.dataframe2_scalebar.elementPositionX -= 100

        self.legend_title.elementPositionX -= 10
        self.legend_df1.elementPositionX -= 10
        self.legend_df2.elementPositionX -= 100
        print 'd1 width', self.dataframe1.elementWidth
        self.dataframe1.elementWidth -= 10
        print 'd1 width', self.dataframe1.elementWidth
        self.dataframe2.elementPositionX -= 100

    def normalizeBreakValues(self, values):
        return [ math.floor(val) if index == 0 else math.ceil(val) for index, val in enumerate(values)]

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

        # Diálogo nativo para elegir fichero
        dlg = QFileDialog()
        dlg.setFileMode(QFileDialog.ExistingFile)
        # Solo mostrar archivos con extensión shp
        dlg.setFilter("shapefile (*.shp)")

        if dlg.exec_():
            # Obtenemos la ruta del archivo
            filepath = map(str, list(dlg.selectedFiles()))[0]

            # Eliminamos las capas (que hayan) en los dataframes
            self.deleteLayers()

            # Mostramos la ruta en el label
            self.label_shp_path.setText(filepath)

            # Creamos la capa a partir de la ruta
            layer = mapping.Layer(filepath)

            # Añadimos la capa a los dataframes
            self.addLayer(layer)

            # Actualizamos la simbología de las capas del dataframe
            [mapping.UpdateLayer(df, l, self.GRADUATED_COLORS) for df in self.dataframes for l in mapping.ListLayers(self.mxd, '', df)]

            # Creamos una variable de clase que contendrá las capas
            self.layers = mapping.ListLayers(self.mxd)

            # Obtenemos los campos de la capa
            fieldnames = map(lambda x: x.name, arcpy.ListFields(layer.dataSource))
            # print fieldnames

            # Limpiamos los valores que haya en los comboboxes
            [combo.clear() for combo in self.comboboxes]
            # Añadimos los valores de los campos del shapefile
            [combo.addItems(fieldnames) for combo in self.comboboxes]
            #print self.mxd, self.dataframes, self.layers

            # Activamos los checkboxes
            [check.setEnabled(True) for check in self.checkboxes]


    def deleteLayers(self):
        '''
        @param: self
        @brief: Elimina las capas de los dataframes
        :return: None
        '''
        [mapping.RemoveLayer(df, l) for df in self.dataframes for l in mapping.ListLayers(self.mxd, '', df)]
        #print 'layers', mapping.ListLayers(self.mxd)

    def addLayer(self, l):
        '''
        @param: self
        @param l : Capa a añadir
        @brief: Añade la capa pasada a los dataframes
        :return: None
        '''
        [mapping.AddLayer(df, l) for df in self.dataframes]

    def loadLYR(self):
        '''
        @param: self
        @brief: Carga el fichero lyr de simbología (GRADUATED_COLORS)
        :return: None
        '''
        self.GRADUATED_COLORS = mapping.Layer(GRADUATED_COLORS_LYR_PATH)

    def loadMXD(self):
        '''
        @param: self
        @brief: Carga el archivo mxd
        :return: None
        '''

        # Cargamos el mxd
        self.mxd = mapping.MapDocument(MXD_PATH)
        # Obtenemos los dataframes
        self.dataframes = mapping.ListDataFrames(self.mxd)

        # Activamos los componentes que están inactivos por defecto
        # (checkboxes, lineedit, ...)
        self.txt_title.setEnabled(True)
        self.check_scale.setEnabled(True)
        self.check_legend.setEnabled(True)
        self.line_edit_df_1.setEnabled(True)
        self.line_edit_df_2.setEnabled(True)

        # Añadimos los nombres de los dataframes a los LineEdits
        self.line_edit_df_1.setText(self.dataframes[0].name)
        self.line_edit_df_2.setText(self.dataframes[1].name)

        # Obtenemos los elementos del Layout que nos interesan
        # para generar los dos tipos de mapas (moviendo los elementos)
        self.dataframe1_scalebar = mapping.ListLayoutElements(self.mxd, '', 'data-frame-1-scale-bar')[0]
        self.dataframe1_scaletext = mapping.ListLayoutElements(self.mxd, '', 'data-frame-1-scale-text')[0]
        self.dataframe2_scalebar = mapping.ListLayoutElements(self.mxd, '', 'data-frame-2-scale-bar')[0]
        self.dataframe2_scaletext = mapping.ListLayoutElements(self.mxd, '', 'data-frame-2-scale-text')[0]

        self.legend_title = mapping.ListLayoutElements(self.mxd, '', 'legend-title')[0]
        self.legend_df1 = mapping.ListLayoutElements(self.mxd, '', 'legend-df-1')[0]
        self.legend_df2 = mapping.ListLayoutElements(self.mxd, '', 'legend-df-2')[0]

        self.map_title = mapping.ListLayoutElements(self.mxd, '', 'title')[0]

        self.dataframe1 = mapping.ListLayoutElements(self.mxd, '', 'data-frame-1')[0]
        self.dataframe2 = mapping.ListLayoutElements(self.mxd, '', 'data-frame-2')[0]




app = QtGui.QApplication(sys.argv)
myDialog = MyDialogClass(None)
myDialog.show()
app.exec_()
```

# Resultados 
***

En este apartado se muestran los enlaces hacia cada uno de los resultados:

- [Mapas temáticos sin escala](https://github.com/joseahr/arcpy-awesome-symbolizer/tree/master/results/no-scale)
- [Mapas temáticos sin leyenda](https://github.com/joseahr/arcpy-awesome-symbolizer/tree/master/results/no-legend)
- [Mapas temáticos sin leyenda y sin escala](https://github.com/joseahr/arcpy-awesome-symbolizer/tree/master/results/no-legend-no-scale)
- [Mapas temáticos completos (con leyenda y escala)](https://github.com/joseahr/arcpy-awesome-symbolizer/tree/master/results/complete)

# Conclusiones
***

Se ha obtenido una buena herramienta para realizar mapas temáticos, a partir de una capa ``shp``, basado en sus atributos.
El diseño del mapa es un diseño simple, sin coordenadas, pero cumple con su función de mostrar atributos temáticos y ser amigable para el usuario final.

En lo que se refiere al formulario, una mejora para la experiencia de usuario, sería utilizar ``QThreads`` y ``QSIGNALS`` para ejecutar ciertas procesos en otro hilo (Para que no interfiera en el hilo de renderizado del ``UI``). Podríamos utilizar esto al cargar los shapefiles y al ejecutar los procesos de impresión de los mapas. De esta manera evitaríamos que el formulario se congelara. Se utilizarían las ``QSIGNALS`` para la comunicación entre el hilo que ejecuta el proceso y el hilo de renderizado.

Se podría añadir también una mejora, para tener el control sobre los ``classBreakValues``, de este modo el usuario pueda cambiar o manejar un redondeo por nuestra cuenta, de modo que sean más legibles en un mapa (por ejemplo si tienen decimales) o para tener rangos de valores más adecuados. [Un intento de esta mejora](https://github.com/joseahr/arcpy-awesome-symbolizer/blob/master/awesome-symbolizer.py#L382) se llevó a cabo sin éxito, ya que los mapas no se imprimían correctamente.