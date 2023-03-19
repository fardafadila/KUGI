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
from qgis.PyQt import QtWidgets, QtCore
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.utils import iface
from qgis.PyQt.QtCore import (
 QAbstractTableModel, 
 QVariant, 
 QStringListModel, 
 pyqtSignal,
 QFileInfo,
 QUrl
)
from qgis.PyQt.QtGui import QDesktopServices
from qgis.core import (
 QgsVectorLayerCache, 
 QgsFeatureRequest, 
 QgsField, 
 QgsProject, 
 QgsWkbTypes,
 QgsCoordinateReferenceSystem,
 QgsVectorLayer,
 QgsVectorFileWriter
 )
from qgis.gui import (
 QgsAttributeTableModel,
 QgsAttributeTableView,
 QgsAttributeTableFilterModel
)



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
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect 
        self.setupUi(self)
        
        ####BUAT TABEL DAFTAR FIELD AWAL
        #definisiin layernya yang dipilih di input combo
        layer = self.inputCombo.currentLayer()
        #self.layer = self.inputCombo.currentLayer()
        prov = layer.dataProvider()
        #dapatkan list field dari layer yang dipilih
        field_names = [field.name() for field in prov.fields()]
        self.fieldTable.clear()
        #buat list nama dan tipe field
        self.namaField = []
        tipeData = []
        #hitung ada berapa field 
        jumlah_field = 0
        #masukin nama dan tipe field ke list
        for count, f in enumerate(field_names):
            self.namaField.append(f)
            jumlah_field +=1
        for field in layer.fields():
            tipe_data = field.typeName()
            tipeData.append(tipe_data)
        #definisiin ada tiga kolom dan buat header
        self.fieldTable.setColumnCount(3)
        self.fieldTable.setHorizontalHeaderLabels(['Nama Kolom', 'Tipe Data', 'Nama Kolom Baru'])
        #atur ukuran kolom terakhir supaya tabel penuh
        self.fieldTable.horizontalHeader().setStretchLastSection(True)

        #buat baris sebanyak jumlah field
        self.fieldTable.setRowCount(jumlah_field)
        for index in range(jumlah_field):
            #buat list item1 untuk nama field
            item1 = QtWidgets.QTableWidgetItem(self.namaField[index])
            #masukkan nama field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,0,item1)
            #buat list item2 untuk tipe field
            item2 = QtWidgets.QTableWidgetItem(tipeData[index])
            #masukkan tipe field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,1,item2)
            combo = QtWidgets.QComboBox()
            #populate the combo box with the field names
            combo.addItems(field_names)
            self.fieldTable.setCellWidget(index,2,combo)

        #atur ukuran tabel
        self.fieldTable.setColumnWidth(0,275)
        self.fieldTable.setColumnWidth(1,185)
        self.kategoriCombo.addItems(daftarKategoriSorted)
        self.kategoriCombo.currentTextChanged.connect(self.populateUnsur)
        #self.outputButton.clicked.connect(self.exportShapefile)
        self.outputButton.clicked.connect(self.outFolder)
        self.inputCombo.currentTextChanged.connect(self.populateTable)
        self.inputCombo.currentTextChanged.connect(self.makeCombo)
        self.unsurCombo.currentTextChanged.connect(self.getUnsurCombo)
        self.unsurCombo.currentTextChanged.connect(self.populateCombo)
        self.runButton.clicked.connect(self.set_att_value)
        self.cancelButton.clicked.connect(self.coba_rename)
        self.comboBox = QtWidgets.QComboBox()

    
    def changeKategori(self):
        try:
            #self.progdialog()  
            urlKategori = "https://kugi.ina-sdi.or.id:8080/kugiapi/featurecatalog"
            response = request.urlopen(urlKategori)
            dataKategori = json.loads(response.read())  
            #buat list daftar id kategori
            daftarID =[]
            #parsing untuk dapat list id kategori dari api
            for dataID in dataKategori:
                id = dataID.get('id')
                idKategori = id.strip('@en')
                daftarID.append(idKategori)  
            #buat zip untuk gabung id dan nama kategori      
            zippedKategori = zip(daftarID, daftarKategori)
            #definisi nama kategori yang dipiih
            selectedCategory = self.kategoriCombo.currentText()
            #ambil id kategori
            for a, b in zippedKategori:
                #buat kondisi untuk dapat id kategori dari nama kategori yang dipilih
                if b == selectedCategory:  
                    inputID = str(a)
                    #buat url api dari id kategori yang dipakai
                    url = "https://kugi.ina-sdi.or.id:8080/kugiapi/featuretype?fcid="
                    response = request.urlopen(url+inputID)
                    data = json.loads(response.read())
                
                    #buat daftar unsur dari api unsur (nama dan kode)
                    daftarUnsurUnordered= []
                    daftarKode =[]
                    listNama = []
                    self.namaUnsurGlobal = []
                
                    for listdata in data:
                        #parsing api unsur untuk dapat nama dan kode unsur dan masukin ke daftar kode dan daftar unsur
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
                        display = namaUnsur  + " | " + kode1 + " \nSkala: " + skala + '\n' + definisi
                        daftarKode.append(kode1)
                        daftarUnsurUnordered.append(display) 
                        listNama.append(namaUnsur)
                        self.namaUnsurGlobal.append(namaUnsur)
                        #nambah tiap hasil parsing nama unsur ke unsurCombo
                        ######zipUnsur itu dict kode dan nama aja, daftarUnsur itu list display lengkap
                    daftarUnsur = sorted(daftarUnsurUnordered)
                    zipUnsur = dict(zip(daftarKode, listNama))
            return(zipUnsur, daftarUnsur)
        
        except :
            self.iface.messageBar().pushMessage('Periksa koneksi internet Anda',level=Qgis.Critical, duration=5)
            
            self.namaUnsurGlobal = None
            zipUnsur = None
            daftarUnsur = None
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
        self.namaUnsurGlobal
        if self.namaUnsurGlobal == None :
            self.namaUnsurGloball = []
        else:
            self.namaUnsurGloball = sorted(self.namaUnsurGlobal) 
        filteredDisplay = []

        if daftarUnsur == None :
            daftarUnsur1 = []
        else:
            daftarUnsur1 =sorted(daftarUnsur)

        self.daftarUnsur = daftarUnsur1 

        filteredDisplay = []

        layer = self.inputCombo.currentLayer()

        if layer == None :
            filteredDisplay = []
        else :


            if layer.geometryType() == 2 :
                x = 0
                for a in self.namaUnsurGloball :
                    if ((self.namaUnsurGloball [x])[-2:]) == 'AR' :
                        filteredDisplay.append(daftarUnsur1[x])
                
                    else :
                        pass
                    x = x + 1   
            if layer.geometryType() == 0 :
                x = 0
                for a in self.namaUnsurGloball :
                    if ((self.namaUnsurGloball [x])[-2:]) == 'PT' :
                        filteredDisplay.append(daftarUnsur1[x])
                
                    else :
                        pass
                    x = x + 1   

            if layer.geometryType() == 1 :
                x = 0
                for a in self.namaUnsurGloball :
                    if ((self.namaUnsurGloball [x])[-2:]) == 'LN' :
                        filteredDisplay.append(daftarUnsur1[x])
                
                    else :
                        pass
                    x = x + 1   
            else:
                print("error")
        self.unsurCombo.clear()  
        self.unsurCombo.setModel(QStringListModel(filteredDisplay))
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
        # Clear the table
        self.fieldTable.clearContents()

        # Get the current layer
        layer = self.inputCombo.currentLayer()

        # Get the list of field names and types
        field_names = [field.name() for field in layer.fields()]
        field_types = [field.typeName() for field in layer.fields()]

        # Set the number of rows and columns in the table
        num_rows = len(field_names)
        self.fieldTable.setRowCount(num_rows)
        self.fieldTable.setColumnCount(3)

        # Set the header labels
        header_labels = ['Nama Kolom', 'Tipe Data', 'Nama Kolom Baru']
        self.fieldTable.setHorizontalHeaderLabels(header_labels)

        # Create a combo box for each row and add it to the table
        for i in range(num_rows):
            # Add the field name to the first column
            field_name_item = QtWidgets.QTableWidgetItem(field_names[i])
            self.fieldTable.setItem(i, 0, field_name_item)

            # Add the field type to the second column
            field_type_item = QtWidgets.QTableWidgetItem(field_types[i])
            self.fieldTable.setItem(i, 1, field_type_item)

            # Create a combo box for the third column
            combo_box_item = QtWidgets.QComboBox()
            self.fieldTable.setCellWidget(i, 2, combo_box_item)

            # Connect the currentIndexChanged signal of each combo box to the update_table_color function
            combo_box_item.currentIndexChanged.connect(lambda index, row=i: self.update_table_color(row, index))

        # Resize the columns to fit the contents
        self.fieldTable.resizeColumnsToContents()

        return jumlah_field

        """
        #definisiin layernya yang dipilih di input combo
        layer = self.inputCombo.currentLayer()
        prov = layer.dataProvider()
        #dapatkan list field dari layer yang dipilih
        field_names = [field.name() for field in prov.fields()]
        self.fieldTable.clear()
        #buat list nama dan tipe field
        namaField = []
        tipeData = []
        #hitung ada berapa field 
        jumlah_field = 0
        #masukin nama dan tipe field ke list
        for count, f in enumerate(field_names):
            namaField.append(f)
            jumlah_field +=1
        for field in layer.fields():
            tipe_data = field.typeName()
            tipeData.append(tipe_data)
        #definisiin ada tiga kolom dan buat header
        self.fieldTable.setColumnCount(3)
        self.fieldTable.setHorizontalHeaderLabels(['Nama Kolom', 'Tipe Data', 'Nama Kolom Baru'])
        #atur ukuran kolom terakhir supaya tabel penuh
        self.fieldTable.horizontalHeader().setStretchLastSection(True)

        #buat baris sebanyak jumlah field
        self.fieldTable.setRowCount(jumlah_field)
        for index in range(jumlah_field):
            #buat list item1 untuk nama field
            item1 = QtWidgets.QTableWidgetItem(namaField[index])
            #masukkan nama field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,0,item1)
            #buat list item2 untuk tipe field
            item2 = QtWidgets.QTableWidgetItem(tipeData[index])
            #masukkan tipe field secara berulang tiap baris dengan index
            self.fieldTable.setItem(index,1,item2)

            # Create a combo box item for each row and add it to the table
            combo_box_item = QtWidgets.QComboBox()
            combo_box_item.addItems([self.ui.comboBox.itemText(i) for i in range(self.ui.comboBox.count())])
            self.fieldTable.setCellWidget(index, 2, combo_box_item)

            # Connect the currentIndexChanged signal of each combo box to the update_table_color function
            combo_box_item.currentIndexChanged.connect(lambda index, row=index: self.update_table_color(row, index))
            
        #atur ukuran tabel
        self.fieldTable.setColumnWidth(0,275)
        self.fieldTable.setColumnWidth(1,185)
        return(jumlah_field)
        """
    
    # Fungsi menghijaukan 
    def update_table_color(row, index):
        color = QColor("#00FF00")  # set the color to green, change this to any other color as desired
        selected_items = []
        for row in range(self.fieldTable.rowCount()):
            combo_box_item = self.fieldTable.cellWidget(row, 2)
            current_text

    def makeCombo(self):
        self.comboBox = None  # initialize comboBox attribute to None
        jumlah_field = self.populateTable()
        if jumlah_field:
            self.comboBox = QtWidgets.QComboBox()  # create new comboBox
            self.fieldTable.setCellWidget(jumlah_field-1, 2, self.comboBox)
            self.populateCombo(self.comboBox.currentText())
        return self.comboBox
    
    def getStrukturList(self):
        dialog, label = self.progdialog()
        zipUnsur,_ = self.changeKategori() #list kode dan nama unsur
        inputUnsur = self.getUnsurCombo() #current text unsur untuk url parse struktur
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
        #INI LIST TIPE DATA YANG MATCH
        self.tipedataMatched = []

        for item in listCombo2:
            textFull = item.currentText()
            text = textFull.split(" ")[0]
            self.matchedList.append(text)
            tipe2 = textFull.split(" ")[-1]
            tipe_data_matched = tipe2.strip(')')
            self.tipedataMatched.append(tipe_data_matched)
        #print (self.tipedataMatched)
        self.namaFieldLayer = []
        layer = self.inputCombo.currentLayer()
        prov = layer.dataProvider()
        field_names = [field.name() for field in prov.fields()] 
        jumlah_field = 0
        #INI LIST TIPE DATA FIELD LAYERNYA
        self.tipeDataLayer = []
        for count, f in enumerate(field_names):
            self.namaFieldLayer.append(f)
            jumlah_field +=1
        for field in layer.fields():
            tipe_data = field.typeName()
            self.tipeDataLayer.append(tipe_data)

        self.zipField = dict(zip(self.namaFieldLayer,self.matchedList))
        self.zipTipeMatched =  [(self.tipeDataLayer[i], self.tipedataMatched[i]) for i in range(0, len(self.tipeDataLayer))]
        #print (self.zipTipeMatched)
        return (self.zipField)

    def coba_rename(self):
        layer = self.inputCombo.currentLayer()
        prov = layer.dataProvider()
        field_names = [field.name() for field in prov.fields()]
        fields = layer.dataProvider().fields()
        #print (fields)
        target_field = "new"
        idx = field_names.index(target_field)
        layer.startEditing()
        layer.deleteAttribute(idx)
        layer.commitChanges()
        #print ("sudah copy value")
    
    def adding_attributes(self):
        #run = self.get_matched()
        #FUNGSI PASTIKAN TIPE DATA MAPPING FIELD SUDAH SAMA
        
        attDict,_, _ = self.getStrukturList()
        layerAwal = self.inputCombo.currentLayer()
        layer = layerAwal.materialize(QgsFeatureRequest().setFilterFids(layerAwal.allFeatureIds()))
        num = 0
        kolomBaru = self.get_matched()
        listDihapus = []
        notMatched = "-"
        for satu, dua in kolomBaru.items():
            if dua != notMatched:
                listDihapus.append(satu)
        #print (listDihapus)
        listAtribut = self.matchedList
        #print (listAtribut)
        listRename = []
        for item in listAtribut:
            if item != "-":
                listRename.append(item)
        #print(listRename)
        listAdd = attDict.copy()
        for key in listRename:
            if key in attDict:
                del listAdd[key]
        #print (listAdd) 
        ####FUNGSI ADD ATRIBUT
        for x, y in attDict.items():
            print ("masuk fungsi penambahan field")
            #print (x)
            num += 1
            if y == "Integer":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Int)])
            elif y == "Int64":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Int64)])
            elif y == "Double":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Double)])
            elif y == "String":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.String)])
            elif y == "OID":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Inte64)])
            elif y == "Date":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.Date)])
            elif y == "Geometry":
                layer.dataProvider().addAttributes([QgsField(x, QVariant.String)])
            else:
                self.QtWidgets.QMessageBox.warning("Tipe data tidak sesuai")
        layer.commitChanges()
        ####END FUNGSI ADD ATRIBUT

        #FUNGSI BUAT COPY VALUE DARI FIELD AWAL KE AKHIR
        prov = layer.dataProvider()
        field_names = [field.name() for field in prov.fields()]
        fields = layer.dataProvider().fields()
        for awal, akhir in kolomBaru.items():
            print ("masuk fungsi copy value")
            #KALAU PADANANNYA BUKAN -
            if akhir != notMatched:            
                #print ("masuk fungsi copy value")
                
                origin_field = awal
                target_field = akhir
                idx = field_names.index(target_field)
                idy = field_names.index(origin_field)
                #print (fields)
                for field in fields:
                    layer.startEditing()
                    for feat in layer.getFeatures():
                        #print (feat[origin_field])
                        layer.changeAttributeValue(feat.id(), idx, feat[origin_field])
                #layer.deleteAttribute(idy)
                layer.commitChanges()
                            
        self.listFieldKugi = []
        prov = layer.dataProvider()
        field_namesUpdated = [field.name() for field in prov.fields()] 
        jumlah_fieldUpdated = 0
        self.namaFieldLayerUpdated= []
        for count, f in enumerate(field_namesUpdated):
            self.namaFieldLayerUpdated.append(f)
            jumlah_fieldUpdated +=1
        print (self.namaFieldLayerUpdated)
        layer.startEditing()
        for namaKolom in self.namaFieldLayerUpdated:
            for harusDihapus in listDihapus:
                if namaKolom == harusDihapus:
                    print ("masuk hapus")
                    idx = layer.fields().indexFromName(namaKolom)
                    print(idx)
                    layer.deleteAttribute(idx)
            layer.updateFields()
        layer.commitChanges()
        return (layer, self.namaFieldLayerUpdated)

    def set_att_value (self):
        self.layerHasil, _ = self.adding_attributes()
        _, mauDiisi = self.adding_attributes()
        attDict,_, _ = self.getStrukturList()
        _, inputKode, _ = self.getStrukturList()
        fcode = str(inputKode)
        self.layerHasil.startEditing()
        prov = self.layerHasil.dataProvider()
        crsLayer1 = self.layerHasil.crs()
        crsLayer = str(crsLayer1).strip('<QgsCoordinateReferenceSystem: EPSG:>')
        field_names = [field.name() for field in prov.fields()]
        for count, f in enumerate(field_names):
            self.namaField.append(f)
        for x in mauDiisi:
            if  x== "FCODE":
                self.layerHasil.dataProvider().addAttributes([QgsField(x, QVariant.Int)])
                field_idx = self.layerHasil.fields().indexOf('FCODE')
                fcode_value = fcode
                for feat in self.layerHasil.getFeatures():
                    self.layerHasil.changeAttributeValue(feat.id(), field_idx, fcode_value)
            elif x == "SRS_ID":
                self.layerHasil.dataProvider().addAttributes([QgsField(x, QVariant.Int)])
                field_idx = self.layerHasil.fields().indexOf('SRS_ID')
                srs_value = crsLayer
                for feat in self.layerHasil.getFeatures():
                    self.layerHasil.changeAttributeValue(feat.id(), field_idx, srs_value)
                
        self.layerHasil.commitChanges()        
        shapefileName = self.getOutFolder()
        if shapefileName == "":
            QgsProject.instance().addMapLayer(self.layerHasil) 
        else:
            crs = QgsCoordinateReferenceSystem()
            crs.createFromId(QgsProject.instance().crs().postgisSrid())
            writer = QgsVectorFileWriter.writeAsVectorFormat(self.layerHasil, shapefileName, "utf-8", crs, "ESRI Shapefile")
            fileInfo = QFileInfo(shapefileName)
            baseName = fileInfo.baseName()
            self.layer = QgsVectorLayer(shapefileName, baseName, "ogr")
            QgsProject.instance().addMapLayer(self.layer) 

    def outFolder(self):
        outFolder = QgsProject.instance().homePath()
        # Get the text from the QLineEdit and use it as the shapefile name
        shapefileName, _ = QFileDialog.getSaveFileName(self, "Save Shapefile", outFolder, "ESRI Shapefile (*.shp)")
        self.saveEdit.insert(shapefileName)
      
    def getOutFolder(self):
        return(self.saveEdit.text())
    

    """def exportShapefile(self): 
        # Get the output folder path from the user
        outFolder = QgsProject.instance().homePath()
        layerDisave = self.layerHasil

        # Get the text from the QLineEdit and use it as the shapefile name
        shapefileName, _ = QFileDialog.getSaveFileName(self, "Save Shapefile", outFolder, "ESRI Shapefile (*.shp)")

        if not shapefileName:
            # User clicked cancel or didn't provide a filename
            return

        # Get the geometry type from the selected layer
        geometryType = self.layerHasil.geometryType()

        # Get the current project CRS
        crs = QgsCoordinateReferenceSystem()
        crs.createFromId(QgsProject.instance().crs().postgisSrid())

        # Write the layer to a shapefile in the specified output folder
        writer = QgsVectorFileWriter.writeAsVectorFormat(layerDisave, shapefileName, "utf-8", crs, "ESRI Shapefile")

        if writer[0] == QgsVectorFileWriter.NoError:
            print("Shapefile exported successfully")
            # Adding shapefile to QGIS Project
            fileInfo = QFileInfo(shapefileName)
            baseName = fileInfo.baseName()
            self.layer = QgsVectorLayer(shapefileName, baseName, "ogr")
            QgsProject.instance().addMapLayer(layerDisave)
        else:
            print("Error exporting shapefile:", writer)"""
