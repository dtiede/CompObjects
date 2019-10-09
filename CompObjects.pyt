import arcpy
default_encoding = sys.getdefaultencoding()
def AddMsgAndPrint(message):
        arcpy.AddMessage(message)
        #print message
        return 0
class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Compare Objects"
        self.alias = ""

        # List of tool classes associated with this toolbox
        self.tools = [CompObjects]

class CompObjects(object):
    def __init__(self):
        self.label = "Compare objects"
        #self.category = ""
        self.description = '''Compares objects (polygons) from a reference layer with another layer'''
        self.canRunInBackground = False

    def getParameterInfo(self):
        refLayer = arcpy.Parameter(
            displayName="Reference layer",
            name="ref_layer",
            # FIXME datatype="GPFeatureLayer",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input")

        inputLayer = arcpy.Parameter(
            displayName="Input layer",
            name="input_layer",
            # FIXME datatype="GPFeatureLayer",
            datatype="Feature Layer",
            parameterType="Required",
            direction="Input")
        fldName = arcpy.Parameter(
            displayName="Field prefix (5 characters max)",
            name="prefix",
            # FIXME datatype="GPFeatureLayer",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        fldName.value = "valid"
        distance = arcpy.Parameter(
            displayName="Max distance between objects",
            name="distance",
            # FIXME datatype="GPFeatureLayer",
            datatype="GPDouble",
            parameterType="Required",
            direction="Input")
        distance.value = 0
        params = [refLayer, inputLayer, fldName, distance]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""

        return

##    def _escape(self, value):
##        return value.replace('\\\\', '\\').replace("'", "\\'").replace(";", "\;")

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""

        if len(parameters[2].valueAsText) > 5:
            parameters[2].setErrorMessage("'prefix' should not exceed 5 characters")
        return


    def execute(self, parameters, messages):
        # fields
        fld_gd = parameters[2].valueAsText + "_gd"
        fld_gd_ID = parameters[2].valueAsText + "_gdid"
        fld_bad = parameters[2].valueAsText + "_bad"
        fld_all = parameters[2].valueAsText + "_all"
        fld_gd_area = parameters[2].valueAsText + "_gdar"
        fld_bigarea = parameters[2].valueAsText + "_big"
        fld_allarea = parameters[2].valueAsText + "_alar"
        refLayer = parameters[0].valueAsText
        inputLayer = parameters[1].valueAsText
        dist = parameters[3].value
        arcpy.AddField_management(refLayer, fld_bigarea, "Double", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(refLayer, fld_gd, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(refLayer, fld_gd_ID, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(refLayer, fld_gd_area, "Double", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(refLayer, fld_bad, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(refLayer, fld_all, "LONG", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        arcpy.AddField_management(refLayer, fld_allarea, "Double", "", "", "", "", "NULLABLE", "NON_REQUIRED", "")
        scratchworkspace = "in_memory"
##Cursor Loop 1 for calculating the relative area overlapping per reference unit
        fields = fields = ("SHAPE@", fld_bigarea)
        with arcpy.da.UpdateCursor(refLayer, fields) as cur:
            AddMsgAndPrint("Update cursor 1 created")
            arcpy.MakeFeatureLayer_management(inputLayer, scratchworkspace + "\\clSelection")
            x= 0
            for row in cur:
                    ##overlapArea = 0
                    theLargest = 0
                    testArea = 0
                    feat = row[0]
                    arcpy.SelectLayerByLocation_management(scratchworkspace + "\\clSelection", "INTERSECT", feat)
                    AddMsgAndPrint ("number of features selected:" + str(arcpy.GetCount_management("in_memory\\clSelection").getOutput(0)))

                    with arcpy.da.SearchCursor(scratchworkspace + "\\clSelection", ["SHAPE@"]) as cur2:
                        for row2 in cur2:
                                feat2 = row2[0]
                                clipPoly = feat.intersect(feat2,4)
                                testArea = clipPoly.area
                                if testArea > theLargest:
                                    theLargest = testArea
                                ##overlapArea = overlapArea + clipPoly.area
                    row[1] = theLargest
                    cur.updateRow(row)
                    x=x+1
                    AddMsgAndPrint ("Reference object overlapping area updated, Unit: " + str(x))
        arcpy.Delete_management(scratchworkspace + "\\clSelection")
##############################################################################
        fields = (fld_bigarea, "SHAPE@", fld_gd, fld_bad, fld_gd_ID, fld_gd_area,fld_all, fld_allarea)
        theList = []
        cur = arcpy.UpdateCursor(refLayer, "", "", "", fld_bigarea + " D")
        #with arcpy.da.UpdateCursor(refLayer, fields) as cur:
            ##cur = sorted(cur)
        AddMsgAndPrint("Update cursor sorted")
        arcpy.MakeFeatureLayer_management(inputLayer, scratchworkspace + "\\clSelection")
        x= 0
        for row in cur:
                AddMsgAndPrint("Area covered by largest patch in reference unit: " + str(row.getValue(fld_bigarea)))
                gd = 0
                allOverlapping = 0
                bad = 0
                gdFID = 999999
                feat = row.shape
                theLargest = 0
                theArea = 0
                allArea = 0
                #Buffer feature with distance value
                if float(dist) >0:
                    featBuff = feat.buffer(dist)
                else:
                    featBuff = feat
                arcpy.SelectLayerByLocation_management(scratchworkspace + "\\clSelection", "INTERSECT", featBuff)
                AddMsgAndPrint ("number of features selected:" + str(arcpy.GetCount_management("in_memory\\clSelection").getOutput(0)))


## cacl real area not buffer for . ok
## good only good in referecne with the highest area ratio
## buffer im zweiten Durchlauf und nur f?r referenzen die noch keinne good haben


                #fields = ("SHAPE@AREA")
                with arcpy.da.SearchCursor(scratchworkspace + "\\clSelection", ["SHAPE@", "FID"]) as cur2:
                    for row2 in cur2:
                        allOverlapping+=1
                        feat2 = row2[0]
                        clipPoly = feat.intersect(feat2,4)
                        allArea = allArea + clipPoly.area
                        if row2[1] not in theList:
                            #feat2 = row2[0]
                            #clipPoly = feat.intersect(feat2,4)
                            if clipPoly.area == 0:
                                clipPoly = featBuff.intersect(feat2,4)
                            testArea = clipPoly.area
                            if testArea > theLargest:
                                gd=1
                                gdFID = row2[1]
                                theLargest = testArea
                                theArea = feat.intersect(feat2,4).area

##                    row[2] = gd
##                    row[3] = allOverlapping - gd
##                    row[4] = gdFID
##                    row[5] = theArea
##                    row[6] =allOverlapping
##fields = (fld_area, "SHAPE@", fld_gd, fld_bad, fld_gd_ID, fld_gd_area, fld_all)
                row.setValue(fld_gd, gd)
                row.setValue(fld_bad, allOverlapping - gd)
                row.setValue(fld_gd_ID, gdFID)
                row.setValue(fld_gd_area, theArea)
                row.setValue(fld_all, allOverlapping)
                row.setValue(fld_allarea, allArea)
                theList.append(gdFID)
                cur.updateRow(row)
                x=x+1
                AddMsgAndPrint ("Reference object updated, Unit: " + str(x))
        AddMsgAndPrint(theList)
        del row
        del cur
        return

