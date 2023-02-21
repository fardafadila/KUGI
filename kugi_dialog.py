# -*- coding: utf-8 -*-
"""
/***************************************************************************
 kugiDialog
                                 A QGIS plugin
 Mengubah struktur data atribut sesuai standar KUGI
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2022-12-26
        git sha              : $Format:%H$
        copyright            : (C) 2022 by UGM
        email                : fardafadila48@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import json
from urllib import request
from time import time, gmtime, strftime

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets, QtCore, QtGui
from qgis.utils import iface
from qgis.PyQt.QtCore import QAbstractTableModel, QVariant, QStringListModel, pyqtSignal
from qgis.core import (QgsVectorLayerCache, 
    QgsFeatureRequest, 
    QgsField, 
    QgsProject,
    QgsWkbTypes,
    QgsVectorFileWriter,
    QgsCoordinateReferenceSystem,
    QgsVectorLayer)
from qgis.gui import (QgsAttributeTableModel,
    QgsAttributeTableView,
    QgsAttributeTableFilterModel)

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'kugi_dialog_base.ui'))

UmumMasuk = pyqtSignal()
urlKategori = "https://kugi.ina-sdi.or.id:8080/kugiapi/featurecatalog"


response = request.urlopen(urlKategori)
dataKategori = json.loads(response.read())
daftarKategori = []

for kategoriList in dataKategori:
    namaKategori = kategoriList.get('name')
    trimmedKategori = namaKategori.strip('@en')
    daftarKategori.append(trimmedKategori)
daftarKategoriSorted = sorted(daftarKategori)


class kugiDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(kugiDialog, self).__init__(parent)
        self.setupUi(self)
        
        #### BUAT TABEL DAFTAR FIELD AWAL
        # definisiin layernya yang dipilih di input combo
        layer = self.inputCombo.currentLayer()
        prov = layer.dataProvider()
        # dapatkan list field dari layer yang dipilih
        field_names = [field.name() for field in prov.fields()]
        self.fieldTable.clear()
        # buat list nama dan tipe field
        self.namaField = []
        tipeData = []
        # hitung ada berapa field 
        jumlah_field = 0
        # masukin nama dan tipe field ke list
        for count, f in enumerate(field_names):
            self.namaField.append(f)
            jumlah_field +=1
        for field in layer.fields():
            tipe_data = field.typeName()
            tipeData.append(tipe_data)
        # definisiin ada tiga kolom dan buat header
        self.fieldTable.setColumnCount(3)
        self.fieldTable.setHorizontalHeaderLabels(['Nama Kolom', 'Tipe Data', 'Nama Kolom Baru'])
        # atur ukuran kolom terakhir supaya tabel penuh
        self.fieldTable.horizontalHeader().setStretchLastSection(True)

        # buat baris sebanyak jumlah field
        self.fieldTable.setRowCount(jumlah_field)
        for index in range(jumlah_field):
            # buat list item1 untuk nama field
            item1 = QtWidgets.QTableWidgetItem(self.namaField[index])
            # masukkan nama field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,0,item1)
            # buat list item2 untuk tipe field
            item2 = QtWidgets.QTableWidgetItem(tipeData[index])
            # masukkan tipe field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,1,item2)
            combo = QtWidgets.QComboBox()
            self.fieldTable.setCellWidget(index,2,combo)

        # atur ukuran tabel
        self.fieldTable.setColumnWidth(0,275)
        self.fieldTable.setColumnWidth(1,185)
        self.kategoriCombo.addItems(daftarKategoriSorted)
        self.kategoriCombo.currentTextChanged.connect(self.populateUnsur)
        self.outputButton.clicked.connect(self.outFolder)
        self.inputCombo.currentTextChanged.connect(self.populateTable)
        self.inputCombo.currentTextChanged.connect(self.makeCombo)
        self.unsurCombo.currentTextChanged.connect(self.getUnsurCombo)
        self.unsurCombo.currentTextChanged.connect(self.populateCombo)
        self.runButton.clicked.connect(self.set_att_value)
        self.cancelButton.clicked.connect(self.get_matched)
    
    def changeKategori(self):
        # buat list daftar id kategori
        daftarID =[]
        # parsing untuk dapat list id kategori dari api
        for dataID in dataKategori:
            id = dataID.get('id')
            idKategori = id.strip('@en')
            daftarID.append(idKategori)  
        # buat zip untuk gabung id dan nama kategori      
        zippedKategori = zip(daftarID, daftarKategori)
        # definisi nama kategori yang dipiih
        selectedCategory = self.kategoriCombo.currentText()
        # ambil id kategori
        for a, b in zippedKategori:
            # buat kondisi untuk dapat id kategori dari nama kategori yang dipilih
            if b == selectedCategory:  
                inputID = str(a)
                # buat url api dari id kategori yang dipakai
                url = "https://kugi.ina-sdi.or.id:8080/kugiapi/featuretype?fcid="
                response = request.urlopen(url+inputID)
                data = json.loads(response.read())
                
                # buat daftar unsur dari api unsur (nama dan kode)
                daftarUnsurUnordered= []
                daftarKode =[]
                listNama = []
                for listdata in data:
                    # parsing api unsur untuk dapat nama dan kode unsur dan masukin ke daftar kode dan daftar unsur
                    unsur = listdata.get('typeName')
                    namaUnsur = unsur.strip('@en')
                    code = listdata.get('code')
                    kode1 = code.strip('@en')
                    kode = str(kode1[4:6])
                    if kode== "01":
                        skala = "1:1.000.000" 
                    elif kode== "02":
                        skala  = "1:500.000" 
                    elif kode == "03":
                        skala  = "1:250.000"
                    elif kode == "04":
                        skala  = "1:100.000"
                    elif kode == "05":
                        skala  = "1:50.000"
                    elif kode == "06":
                        skala  = "1:25.000"
                    elif kode == "07":
                        skala  = "1:10.000"
                    elif kode == "08":
                        skala  = "1:5.000"
                    elif kode == "09":
                        skala  = "1:2.500"
                    elif kode == "10":
                        skala  = "1:1.000"
                    else:
                        skala="error"
                    definisi1 = listdata.get('definition')
                    definisi = definisi1.strip('@en')
                    display = namaUnsur  + " | " + kode1+ " \nSkala: " + skala + '\n' + definisi
                    daftarKode.append(kode1)
                    daftarUnsurUnordered.append(display) 
                    listNama.append(namaUnsur)
                    # nambah tiap hasil parsing nama unsur ke unsurCombo
###### zipUnsur itu dict kode dan nama aja, daftarUnsur itu list display lengkap
                daftarUnsur = sorted(daftarUnsurUnordered)
                zipUnsur = dict(zip(daftarKode, listNama))
        return(zipUnsur, daftarUnsur)
    
    def progdialog(self):
        dialog = QtWidgets.QProgressDialog()
        dialog.setWindowTitle("KUGI")
        label = QtWidgets.QLabel(dialog)
        label.setText("Sedang memproses")
        dialog.setMinimumWidth(300)        
        dialog.show()
        return dialog, label
    def populateUnsur(self, progdialog):
        dialog, label = self.progdialog()       
        _, daftarUnsur = self.changeKategori()
        self.unsurCombo.clear()  
        self.unsurCombo.setModel(QStringListModel(daftarUnsur))
        self.listView = QtWidgets.QListView()
        self.listView.setWordWrap(True)
        self.unsurCombo.setView(self.listView)
        self.unsurCombo.show()
        #progress = 100

    def getUnsurCombo(self):
        a = self.unsurCombo.currentText()
        b = str(a.split(" ")[0])
        return(b)

    def populateTable(self):
        # definisiin layernya yang dipilih di input combo
        layer = self.inputCombo.currentLayer()
        prov = layer.dataProvider()
        # dapatkan list field dari layer yang dipilih
        field_names = [field.name() for field in prov.fields()]
        self.fieldTable.clear()
        # buat list nama dan tipe field
        namaField = []
        tipeData = []
        # hitung ada berapa field 
        jumlah_field = 0
        # masukin nama dan tipe field ke list
        for count, f in enumerate(field_names):
            namaField.append(f)
            jumlah_field +=1
        for field in layer.fields():
            tipe_data = field.typeName()
            tipeData.append(tipe_data)
        # definisiin ada tiga kolom dan buat header
        self.fieldTable.setColumnCount(3)
        self.fieldTable.setHorizontalHeaderLabels(['Nama Kolom', 'Tipe Data', 'Nama Kolom Baru'])
        # atur ukuran kolom terakhir supaya tabel penuh
        self.fieldTable.horizontalHeader().setStretchLastSection(True)

        # buat baris sebanyak jumlah field
        self.fieldTable.setRowCount(jumlah_field)
        for index in range(jumlah_field):
            # buat list item1 untuk nama field
            item1 = QtWidgets.QTableWidgetItem(namaField[index])
            # masukkan nama field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,0,item1)
            # buat list item2 untuk tipe field
            item2 = QtWidgets.QTableWidgetItem(tipeData[index])
            # masukkan tipe field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,1,item2)
        # atur ukuran tabel
        self.fieldTable.setColumnWidth(0,275)
        self.fieldTable.setColumnWidth(1,185)
        return(jumlah_field)
        
    def makeCombo(self):
        jumlah_field = self.populateTable()
        self.listCombo= []
        for index in range(jumlah_field):
            combo = QtWidgets.QComboBox()
            self.listCombo.append(combo)
            self.fieldTable.setCellWidget(index,2,combo)
        return(self.listCombo)    
    
    def getStrukturList(self):
        dialog, label = self.progdialog()
        zipUnsur,_ = self.changeKategori() # list kode dan nama unsur
        inputUnsur = self.getUnsurCombo() # current text unsur untuk url parse struktur
        for a, b in zipUnsur.items():
            if b == inputUnsur:
                inputKode = str(a)
                urlStruktur = 'https://kugi.ina-sdi.or.id:8080/kugiapi/featuretypegetbycode?code='
                responseStruktur = request.urlopen(urlStruktur+inputKode)
                data = json.loads(responseStruktur.read())
                displayDaftarStrukturRedundan =['-']
                daftarStruktur =[]
                tipeDataStruktur = []
                for listStruktur in data:
                    struktur = listStruktur.get('ptMemberName')
                    definisi = listStruktur.get('ptDefinition')
                    tipeData = listStruktur.get('faValueType')
                    fcode = listStruktur.get('code')
                    displayStruktur = struktur + ' | '  +definisi + ' (Tipe data: ' + tipeData + ')'
                    daftarStruktur.append(struktur)
                    tipeDataStruktur.append(tipeData)
                    displayDaftarStrukturRedundan.append(displayStruktur)                
                displayDaftarStrukturUnordered = [*set(displayDaftarStrukturRedundan)]
                displayDaftarStruktur = sorted(displayDaftarStrukturUnordered)
                dictStrukturTipe = dict(zip(daftarStruktur, tipeDataStruktur))
        return(dictStrukturTipe, inputKode, displayDaftarStruktur)
    
    def populateCombo(self):
        dialog, label = self.progdialog()
        _, _, displayDaftarStruktur = self.getStrukturList()
        jumlah_field = self.populateTable()
        for index in range(jumlah_field):
            combo = self.makeCombo()
            cek = self.unsurCombo.currentText()
            if cek == "" :
                skip = []
                for t in skip:
                    for listCombo in combo:
                        listCombo.addItem(t)
            else :
                for t in displayDaftarStruktur:
                    listComboCoba =[]
                    for listCombo in combo:
                        listCombo.addItem(t)
                        listComboCoba.append(listCombo)                    
            self.fieldTable.setCellWidget(index,2,listCombo)
        return(listComboCoba)

    
    def get_matched (self):
        #combo2 = self.populateCombo()
        self.matchedList= []
        listCombo2 = self.listCombo
        for item in listCombo2:
            textFull = item.currentText()
            text = textFull.split(" ")[0]
            self.matchedList.append(text)
        self.zipField = dict(zip(self.namaField,self.matchedList))
        print (self.zipField)

    def adding_attributes(self):
        #run = self.get_matched()
        attDict,_, _ = self.getStrukturList()
        layerAwal = self.inputCombo.currentLayer()
        layer = layerAwal.materialize(QgsFeatureRequest().setFilterFids(layerAwal.allFeatureIds()))
        num = 0
        cobaMatch = self.zipField()
        for x, y in attDict.items():
            num += 1
            if y == "Integer":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Int)])
            elif y == "Int64":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Int64)])
            elif y == "Double":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Double)])
            elif y == "String":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.String)])
            elif y == "Date":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Date)])
        layer.commitChanges()
        return (layer)

    def set_att_value (self):
        layer = self.adding_attributes()
        attDict,_, _ = self.getStrukturList()
        _, inputKode, _ = self.getStrukturList()
        fcode = str(inputKode)
        feats_count = layer.featureCount()
        layer.startEditing()
        prov = layer.dataProvider()
        crsLayer1 = layer.crs()
        crsLayer = str(crsLayer1).strip('<QgsCoordinateReferenceSystem: EPSG:>')
        field_names = [field.name() for field in prov.fields()]
        for count, f in enumerate(field_names):
            self.namaField.append(f)
        for x in self.namaField:
            if  x== "FCODE":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Int)])
                field_idx = layer.fields().indexOf('FCODE')
                fcode_value = fcode
                for feat in layer.getFeatures():
                    layer.changeAttributeValue(feat.id(), field_idx, fcode_value)
            elif x == "SRS_ID":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Int)])
                field_idx = layer.fields().indexOf('SRS_ID')
                srs_value = crsLayer
                for feat in layer.getFeatures():
                    layer.changeAttributeValue(feat.id(), field_idx, srs_value)
                
        layer.commitChanges()        
        QgsProject.instance().addMapLayer(layer) 

    def outFolder(self):
        # Show the folder dialog for output
        self.saveEdit.clear()
        fileDialog = QtWidgets.QFileDialog()
        outFolderName = fileDialog.getExistingDirectory(self, "Open a folder", ".", QtWidgets.QFileDialog.ShowDirsOnly)
        outPath = QtCore.QFileInfo(outFolderName).absoluteFilePath()
        if outFolderName:
            self.saveEdit.clear()
            self.saveEdit.insert(outPath)
      
    def saveFile(self):
        return(self.saveEdit.text())

    def exportShapefile(self):
        # Get the output folder path
        outFolder = self.getOutFolder()

        # Get the text from the QLineEdit and use it as the shapefile name
        shapefileName = self.lineEdit.text()

        # Get the current project CRS
        crs = QgsCoordinateReferenceSystem()
        crs.createFromId(QgsProject.instance().crs().postgisSrid())

        # Create a new vector layer and add it to the project
        if geometryType == QgsWkbTypes.PointGeometry:
            vl = QgsVectorLayer("Point?crs=" + crs.authid(), shapefileName, "memory")
        elif geometryType == QgsWkbTypes.LineGeometry:
            vl = QgsVectorLayer("LineString?crs=" + crs.authid(), shapefileName, "memory")
        elif geometryType == QgsWkbTypes.PolygonGeometry:
            vl = QgsVectorLayer("Polygon?crs=" + crs.authid(), shapefileName, "memory")
        elif geometryType == QgsWkbTypes.Unknown:
            print("Invalid layer type")
            vl = None
        else:
            print("Unhandled geometry type")
            vl = None

        # Add the layer to the project
        if vl is not None:
            QgsProject.instance().addMapLayer(vl)
        else:
            print("Error creating layer")

        # Write the layer to a shapefile in the specified output folder
        writer = QgsVectorFileWriter.writeAsVectorFormat(vl, outFolder + "/" + shapefileName + ".shp", "utf-8", crs, "ESRI Shapefile")

        if writer[0] == QgsVectorFileWriter.NoError:
            print("Shapefile exported successfully")
        else:
            print("Error exporting shapefile:", writer)
